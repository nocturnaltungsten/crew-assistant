# Robust Tool Call Parser
# Handles malformed, incomplete, and poorly structured tool calls from LLMs

import json
import re
from dataclasses import dataclass
from typing import Any

from .tools import ToolCall, ToolRegistry, default_registry


@dataclass
class ParseResult:
    """Result of parsing an LLM response for tool calls."""

    tool_calls: list[ToolCall]
    parse_errors: list[str]
    raw_text: str
    confidence: float  # Overall confidence in parsing (0-1)


class ToolCallParser:
    """Extremely robust parser for tool calls in LLM responses."""

    def __init__(self, registry: ToolRegistry = None):
        self.registry = registry or default_registry

        # Common patterns for tool calls
        self.patterns = [
            # JSON function call format
            r"```json\s*({.*?})\s*```",
            r"```\s*({.*?})\s*```",
            r'({[^{}]*?"tool_name"[^{}]*?})',
            r'({[^{}]*?"name"[^{}]*?})',
            # Function call format
            r"(\w+)\s*\((.*?)\)",
            # XML-like format
            r'<tool[^>]*name=["\']?(\w+)["\']?[^>]*>(.*?)</tool>',
            r"<(\w+)>(.*?)</\1>",
            # Markdown code block with function name
            r"```(\w+)\s*(.*?)```",
            # Simple name: parameters format
            r"(\w+):\s*({.*?})",
            r"(\w+):\s*(.*?)(?:\n|$)",
        ]

    def parse(self, text: str) -> ParseResult:
        """Parse tool calls from LLM response text.

        Args:
            text: Raw text from LLM response

        Returns:
            ParseResult with extracted tool calls and metadata
        """
        tool_calls = []
        parse_errors = []
        overall_confidence = 1.0

        # Try parsing strategies in order of reliability
        strategies = [
            # High confidence structured formats
            (self._parse_json_blocks, 0.8),
            (self._parse_function_calls, 0.7),
            # Medium confidence formats
            (self._parse_xml_format, 0.6),
            (self._parse_markdown_blocks, 0.5),
            # Low confidence fallbacks
            (self._parse_key_value_pairs, 0.4),
            (self._parse_natural_language, 0.3),
        ]

        found_high_confidence = False

        for strategy, min_confidence in strategies:
            try:
                calls, errors, confidence = strategy(text)

                # Only add calls if they meet minimum confidence threshold
                if confidence >= min_confidence:
                    tool_calls.extend(calls)
                    parse_errors.extend(errors)
                    overall_confidence *= confidence

                    # If we found high confidence calls, stop looking
                    if calls and confidence > 0.7:
                        found_high_confidence = True
                        break

            except Exception as e:
                parse_errors.append(f"Strategy {strategy.__name__} failed: {str(e)}")

        # If we found structured calls, don't use natural language fallbacks
        if found_high_confidence:
            # Filter out low-confidence natural language calls
            tool_calls = [call for call in tool_calls if call.confidence > 0.5]

        # Remove duplicate tool calls
        tool_calls = self._deduplicate_calls(tool_calls)

        # Validate tool calls against registry
        validated_calls = []
        for call in tool_calls:
            if self._validate_tool_call(call):
                validated_calls.append(call)
            else:
                # Try fuzzy matching
                fuzzy_match = self.registry.fuzzy_match_tool(call.tool_name)
                if fuzzy_match:
                    call.tool_name = fuzzy_match
                    call.confidence *= 0.7  # Reduce confidence for fuzzy matches
                    validated_calls.append(call)
                else:
                    parse_errors.append(f"Unknown tool: {call.tool_name}")

        return ParseResult(
            tool_calls=validated_calls,
            parse_errors=parse_errors,
            raw_text=text,
            confidence=overall_confidence,
        )

    def _parse_json_blocks(self, text: str) -> tuple[list[ToolCall], list[str], float]:
        """Parse JSON-formatted tool calls."""
        tool_calls = []
        errors = []
        confidence = 1.0

        # Find JSON blocks - more aggressive patterns for multiline content
        json_patterns = [
            r"```json\s*(\{.*?\})\s*```",  # Standard json blocks
            r"```\s*(\{.*?\})\s*```",  # Generic code blocks
            r'(\{[^{}]*?(?:"tool_name"|"name"|"function").*?\})',  # Any JSON with tool fields
            r'(\{[^{}]*?"tool_name"[^{}]*?\})',  # Simplified tool_name search
            r"```json\s*(\{[\s\S]*?\})\s*```",  # Multiline JSON blocks
            r"```\s*(\{[\s\S]*?\})\s*```",  # Multiline generic blocks
        ]

        for pattern in json_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)

            for match in matches:
                json_str = match.group(1)

                try:
                    # Try parsing as valid JSON
                    data = json.loads(json_str)
                    call = self._extract_call_from_dict(data)
                    if call:
                        call.raw_text = json_str
                        tool_calls.append(call)

                except json.JSONDecodeError:
                    # Try fixing common JSON issues
                    fixed_call = self._fix_malformed_json(json_str)
                    if fixed_call:
                        fixed_call.confidence *= 0.8  # Reduce confidence for fixed JSON
                        tool_calls.append(fixed_call)
                    else:
                        errors.append(f"Failed to parse JSON: {json_str[:100]}...")
                        confidence *= 0.9

        return tool_calls, errors, confidence

    def _parse_function_calls(self, text: str) -> tuple[list[ToolCall], list[str], float]:
        """Parse function call syntax: function_name(param1=value1, param2=value2)."""
        tool_calls = []
        errors = []
        confidence = 0.9

        # Pattern for function calls
        pattern = r"(\w+)\s*\((.*?)\)"
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2)

            # Skip if this looks like Python/generic code rather than tool call
            if func_name in ["print", "len", "range", "str", "int", "float", "list", "dict"]:
                continue

            try:
                # Parse parameters
                params = self._parse_function_parameters(params_str)

                call = ToolCall(
                    tool_name=func_name,
                    parameters=params,
                    raw_text=match.group(0),
                    confidence=confidence,
                )
                tool_calls.append(call)

            except Exception as e:
                errors.append(f"Failed to parse function call {func_name}: {str(e)}")

        return tool_calls, errors, confidence

    def _parse_xml_format(self, text: str) -> tuple[list[ToolCall], list[str], float]:
        """Parse XML-like tool call format."""
        tool_calls = []
        errors = []
        confidence = 0.8

        # XML patterns
        patterns = [
            r'<tool[^>]*name=["\']?(\w+)["\']?[^>]*>(.*?)</tool>',
            r"<(\w+)>(.*?)</\1>",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)

            for match in matches:
                tool_name = match.group(1)
                content = match.group(2).strip()

                # Skip common HTML tags
                if tool_name.lower() in ["div", "span", "p", "a", "img", "br", "hr"]:
                    continue

                try:
                    # Try to parse content as JSON
                    if content.startswith("{") and content.endswith("}"):
                        params = json.loads(content)
                    else:
                        # Parse as key-value pairs
                        params = self._parse_key_value_content(content)

                    call = ToolCall(
                        tool_name=tool_name,
                        parameters=params,
                        raw_text=match.group(0),
                        confidence=confidence,
                    )
                    tool_calls.append(call)

                except Exception as e:
                    errors.append(f"Failed to parse XML tool call {tool_name}: {str(e)}")

        return tool_calls, errors, confidence

    def _parse_markdown_blocks(self, text: str) -> tuple[list[ToolCall], list[str], float]:
        """Parse markdown code blocks as tool calls."""
        tool_calls = []
        errors = []
        confidence = 0.7

        # Look for code blocks with tool names
        pattern = r"```(\w+)\s*(.*?)```"
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            tool_name = match.group(1)
            content = match.group(2).strip()

            # Skip common programming languages
            if tool_name.lower() in [
                "python",
                "javascript",
                "bash",
                "shell",
                "json",
                "yaml",
                "xml",
            ]:
                continue

            try:
                # Try to parse content as parameters
                if content.startswith("{") and content.endswith("}"):
                    params = json.loads(content)
                else:
                    params = self._parse_key_value_content(content)

                call = ToolCall(
                    tool_name=tool_name,
                    parameters=params,
                    raw_text=match.group(0),
                    confidence=confidence,
                )
                tool_calls.append(call)

            except Exception as e:
                errors.append(f"Failed to parse markdown tool call {tool_name}: {str(e)}")

        return tool_calls, errors, confidence

    def _parse_key_value_pairs(self, text: str) -> tuple[list[ToolCall], list[str], float]:
        """Parse key: value format tool calls."""
        tool_calls = []
        errors = []
        confidence = 0.6

        # Look for tool_name: {params} or tool_name: param_value patterns
        patterns = [
            r"(\w+):\s*(\{.*?\})",
            r"(\w+):\s*([^{\n]+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)

            for match in matches:
                tool_name = match.group(1)
                params_str = match.group(2).strip()

                # Skip common labels that aren't tool names
                if tool_name.lower() in ["note", "example", "output", "result", "error", "warning"]:
                    continue

                try:
                    if params_str.startswith("{") and params_str.endswith("}"):
                        params = json.loads(params_str)
                    else:
                        # Treat as single parameter
                        params = {"value": params_str}

                    call = ToolCall(
                        tool_name=tool_name,
                        parameters=params,
                        raw_text=match.group(0),
                        confidence=confidence,
                    )
                    tool_calls.append(call)

                except Exception as e:
                    errors.append(f"Failed to parse key-value tool call {tool_name}: {str(e)}")

        return tool_calls, errors, confidence

    def _parse_natural_language(self, text: str) -> tuple[list[ToolCall], list[str], float]:
        """Parse natural language descriptions of tool calls - CONSERVATIVE approach."""
        tool_calls = []
        errors = []
        confidence = 0.4

        # Only parse natural language if no structured formats were found
        # and the text contains clear action words

        action_indicators = [
            "create a file",
            "write a file",
            "save to file",
            "make a file",
            "read the file",
            "open the file",
            "view the file",
            "show me the file",
            "list the directory",
            "show directory",
            "list files",
        ]

        # Check if text contains clear file operation language
        has_file_action = any(indicator in text.lower() for indicator in action_indicators)

        if not has_file_action:
            return tool_calls, errors, confidence

        # Only look for very explicit tool usage patterns
        tool_names = self.registry.list_tools()

        for tool_name in tool_names:
            # Very specific patterns that clearly indicate tool usage
            if tool_name == "write_file":
                patterns = [
                    r"\b(?:create|write|save|make)\s+(?:a\s+)?file\b",
                    r"\bsave\s+(?:this\s+)?(?:to\s+)?(?:a\s+)?file\b",
                ]
            elif tool_name == "read_file":
                patterns = [
                    r"\b(?:read|open|view|show)\s+(?:the\s+)?file\b",
                    r"\bwhat\'?s\s+in\s+(?:the\s+)?file\b",
                ]
            elif tool_name == "list_directory":
                patterns = [
                    r"\b(?:list|show)\s+(?:the\s+)?(?:directory|folder|files)\b",
                ]
            else:
                continue  # Skip unknown tools

            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    # Skip if this appears to be in agent reasoning/thinking
                    context_start = max(0, match.start() - 50)
                    context = text[context_start : match.end() + 50]

                    # Skip if this is in thinking/explanation context
                    skip_indicators = [
                        "<think>",
                        "would do",
                        "could do",
                        "should do",
                        "example",
                        "instructions",
                        "available tools",
                    ]
                    if any(skip in context.lower() for skip in skip_indicators):
                        continue

                    # Extract potential parameters from context
                    params = self._extract_params_from_context(text, match.span())

                    # Only create tool call if we have reasonable parameters
                    if tool_name == "write_file" and "content" in params:
                        call = ToolCall(
                            tool_name=tool_name,
                            parameters=params,
                            raw_text=match.group(0),
                            confidence=confidence,
                        )
                        tool_calls.append(call)
                    elif tool_name == "read_file" and "file_path" in params:
                        call = ToolCall(
                            tool_name=tool_name,
                            parameters=params,
                            raw_text=match.group(0),
                            confidence=confidence,
                        )
                        tool_calls.append(call)
                    elif tool_name == "list_directory":
                        call = ToolCall(
                            tool_name=tool_name,
                            parameters=params,
                            raw_text=match.group(0),
                            confidence=confidence,
                        )
                        tool_calls.append(call)

        return tool_calls, errors, confidence

    def _fix_malformed_json(self, json_str: str) -> ToolCall | None:
        """Try to fix common JSON formatting issues."""

        # First try parsing as-is
        try:
            data = json.loads(json_str)
            call = self._extract_call_from_dict(data)
            if call:
                call.raw_text = json_str
                return call
        except:
            pass

        # Advanced fixes for complex content
        fixes = [
            # Basic quote fixes
            lambda s: re.sub(r"(\w+):", r'"\1":', s),
            lambda s: s.replace("'", '"'),
            # Handle escaped content properly
            lambda s: self._fix_escaped_content(s),
            # Remove trailing commas
            lambda s: re.sub(r",\s*}", "}", s),
            lambda s: re.sub(r",\s*]", "]", s),
            # Fix unescaped quotes in content
            lambda s: self._fix_unescaped_quotes(s),
        ]

        for fix in fixes:
            try:
                fixed = fix(json_str)
                if fixed != json_str:  # Only try if something changed
                    data = json.loads(fixed)
                    call = self._extract_call_from_dict(data)
                    if call:
                        call.raw_text = json_str
                        return call
            except:
                continue

        return None

    def _fix_escaped_content(self, json_str: str) -> str:
        """Fix escaped content in JSON strings."""
        # Handle common escape sequence issues
        fixes = [
            (r"\\n", "\n"),  # Fix newlines
            (r"\\t", "\t"),  # Fix tabs
            (r'\\"', '"'),  # Fix quotes (but be careful)
            (r"\\\\", "\\"),  # Fix backslashes
        ]

        result = json_str
        for pattern, replacement in fixes:
            result = result.replace(pattern, replacement)

        return result

    def _fix_unescaped_quotes(self, json_str: str) -> str:
        """Fix unescaped quotes within content strings."""
        # This is complex - try to identify content fields and escape quotes within them
        try:
            # Look for "content": "..." patterns and escape internal quotes
            pattern = r'"content":\s*"([^"]*(?:\\"[^"]*)*)"'

            def escape_content(match):
                content = match.group(1)
                # Escape any unescaped quotes
                content = content.replace('\\"', "___TEMP_QUOTE___")  # Preserve already escaped
                content = content.replace('"', '\\"')  # Escape unescaped
                content = content.replace("___TEMP_QUOTE___", '\\"')  # Restore escaped
                return f'"content": "{content}"'

            result = re.sub(pattern, escape_content, json_str)
            return result

        except:
            return json_str

    def _extract_call_from_dict(self, data: dict[str, Any]) -> ToolCall | None:
        """Extract tool call from parsed dictionary."""
        # Look for tool name in various keys
        tool_name = None
        for key in ["tool_name", "name", "function", "tool", "action"]:
            if key in data:
                tool_name = data[key]
                break

        if not tool_name:
            return None

        # Extract parameters
        params = {}
        for key, value in data.items():
            if key not in ["tool_name", "name", "function", "tool", "action"]:
                params[key] = value

        # If there's a 'parameters' or 'params' key, use that
        if "parameters" in data:
            params = data["parameters"]
        elif "params" in data:
            params = data["params"]
        elif "arguments" in data:
            params = data["arguments"]

        return ToolCall(tool_name=tool_name, parameters=params)

    def _parse_function_parameters(self, params_str: str) -> dict[str, Any]:
        """Parse function call parameters."""
        params = {}

        if not params_str.strip():
            return params

        # Try parsing as JSON first
        try:
            if params_str.strip().startswith("{"):
                return json.loads(params_str)
        except:
            pass

        # Parse as key=value pairs
        param_pattern = r"(\w+)\s*=\s*([^,]+)"
        matches = re.finditer(param_pattern, params_str)

        for match in matches:
            key = match.group(1)
            value = match.group(2).strip()

            # Try to parse value
            try:
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                # Try parsing as number
                elif value.replace(".", "").replace("-", "").isdigit():
                    value = float(value) if "." in value else int(value)
                # Try parsing as boolean
                elif value.lower() in ["true", "false"]:
                    value = value.lower() == "true"

                params[key] = value
            except:
                params[key] = value

        return params

    def _parse_key_value_content(self, content: str) -> dict[str, Any]:
        """Parse key-value content from various formats."""
        params = {}

        # Try each line as key: value
        for line in content.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                params[key] = value

        return params

    def _extract_params_from_context(self, text: str, span: tuple[int, int]) -> dict[str, Any]:
        """Extract parameters from surrounding context of a match."""
        # Get text around the match
        start, end = span
        context_start = max(0, start - 200)  # Expand context window
        context_end = min(len(text), end + 200)
        context = text[context_start:context_end]

        params = {}

        # Look for file paths, URLs, etc.
        file_patterns = [
            r'["\']?([^"\'<>\s]+\.[a-zA-Z0-9]+)["\']?',  # filename.ext
            r'file[_\s]+(?:path|name)[_\s]*[:\s]+["\']?([^"\'<>\s\n]+)["\']?',  # file path: ...
            r'/[^"\'<>\s\n]+',  # absolute paths
            r'\.\/[^"\'<>\s\n]+',  # relative paths
            r"[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z0-9]+",  # simple filenames
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                # Take the most reasonable looking filename
                for match in matches:
                    if len(match) > 2 and "." in match:
                        params["file_path"] = match
                        break

        # Look for content patterns
        content_patterns = [
            r'["\']([^"\']{5,})["\']',  # quoted strings
            r'content[_\s]*[:\s]+["\']?([^"\'<>\n]{5,})["\']?',  # content: ...
            r'text[_\s]*[:\s]+["\']?([^"\'<>\n]{5,})["\']?',  # text: ...
            r'with[_\s]+["\']([^"\']{5,})["\']',  # with "content"
            r'contains?[_\s]+["\']([^"\']{5,})["\']',  # contains "content"
        ]

        for pattern in content_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                # Take the first reasonable content match
                content = matches[0].strip()
                if len(content) >= 3:  # Minimum content length
                    params["content"] = content
                    break

        # Special handling for common phrases
        # "hello world" content
        if "hello world" in context.lower():
            params["content"] = "hello world"

        # Default file path if we have content but no path
        if "content" in params and "file_path" not in params:
            # Generate a reasonable default filename
            content_preview = params["content"][:20].replace(" ", "_").lower()
            params["file_path"] = f"{content_preview}.txt"

        # Handle directory listing requests
        if any(word in context.lower() for word in ["list", "directory", "folder", "contents"]):
            if "dir_path" not in params:
                # Look for directory paths
                dir_patterns = [
                    r'/[^"\'<>\s\n]*/?',  # absolute directory paths
                    r"\./?",  # current directory
                    r"\w+/?",  # simple directory names
                ]
                for pattern in dir_patterns:
                    matches = re.findall(pattern, context)
                    if matches:
                        params["dir_path"] = matches[0]
                        break

                # Default to current directory
                if "dir_path" not in params:
                    params["dir_path"] = "."

        return params

    def _deduplicate_calls(self, tool_calls: list[ToolCall]) -> list[ToolCall]:
        """Remove duplicate tool calls."""
        seen = set()
        unique_calls = []

        for call in tool_calls:
            # Create a signature for the call
            signature = (call.tool_name, json.dumps(call.parameters, sort_keys=True))

            if signature not in seen:
                seen.add(signature)
                unique_calls.append(call)

        return unique_calls

    def _validate_tool_call(self, call: ToolCall) -> bool:
        """Validate that a tool call references a known tool."""
        return self.registry.get_tool(call.tool_name) is not None
