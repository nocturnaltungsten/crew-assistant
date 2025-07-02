# File Operation Tools
# Basic file read/write tools with safety checks

import pathlib

# Register tools with default registry
from .tools import BaseTool, ToolCallStatus, ToolParameter, ToolResult, default_registry


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Returns the file content as text."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to the file to read (relative or absolute)",
                required=True,
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding (default: utf-8)",
                required=False,
                default="utf-8",
            ),
            ToolParameter(
                name="max_size_mb",
                type="number",
                description="Maximum file size to read in MB (default: 10)",
                required=False,
                default=10,
            ),
        ]

    def execute(
        self, file_path: str, encoding: str = "utf-8", max_size_mb: float = 10
    ) -> ToolResult:
        """Execute file read operation."""
        try:
            # Resolve path
            path = pathlib.Path(file_path).resolve()

            # Security check - ensure file exists and is a file
            if not path.exists():
                return ToolResult(
                    status=ToolCallStatus.ERROR, error_message=f"File does not exist: {file_path}"
                )

            if not path.is_file():
                return ToolResult(
                    status=ToolCallStatus.ERROR, error_message=f"Path is not a file: {file_path}"
                )

            # Size check
            file_size = path.stat().st_size
            max_size_bytes = max_size_mb * 1024 * 1024

            if file_size > max_size_bytes:
                return ToolResult(
                    status=ToolCallStatus.ERROR,
                    error_message=f"File too large: {file_size / 1024 / 1024:.2f}MB (max: {max_size_mb}MB)",
                )

            # Read file
            with open(path, encoding=encoding) as f:
                content = f.read()

            return ToolResult(
                status=ToolCallStatus.SUCCESS,
                content=content,
                metadata={
                    "file_path": str(path),
                    "file_size": file_size,
                    "encoding": encoding,
                    "lines": len(content.splitlines()),
                },
            )

        except UnicodeDecodeError as e:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Failed to decode file with encoding '{encoding}': {str(e)}",
            )
        except PermissionError:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Permission denied reading file: {file_path}",
            )
        except Exception as e:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Unexpected error reading file: {str(e)}",
            )


class WriteFileTool(BaseTool):
    """Tool for writing content to a file."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file. Creates the file if it doesn't exist, or overwrites if it does."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to the file to write (relative or absolute)",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write to the file",
                required=True,
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding (default: utf-8)",
                required=False,
                default="utf-8",
            ),
            ToolParameter(
                name="create_dirs",
                type="boolean",
                description="Create parent directories if they don't exist (default: false)",
                required=False,
                default=False,
            ),
        ]

    def execute(
        self, file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = False
    ) -> ToolResult:
        """Execute file write operation."""
        try:
            # Resolve path
            path = pathlib.Path(file_path).resolve()

            # Check if parent directory exists
            parent_dir = path.parent
            if not parent_dir.exists():
                if create_dirs:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                else:
                    return ToolResult(
                        status=ToolCallStatus.ERROR,
                        error_message=f"Parent directory does not exist: {parent_dir}. Use create_dirs=true to create it.",
                    )

            # Basic safety check - don't write to system directories
            system_dirs = ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/boot", "/sys", "/proc"]
            path_str = str(path)

            for sys_dir in system_dirs:
                if path_str.startswith(sys_dir):
                    return ToolResult(
                        status=ToolCallStatus.ERROR,
                        error_message=f"Cannot write to system directory: {sys_dir}",
                    )

            # Write file
            with open(path, "w", encoding=encoding) as f:
                f.write(content)

            # Verify write
            written_size = path.stat().st_size

            return ToolResult(
                status=ToolCallStatus.SUCCESS,
                content=f"Successfully wrote {len(content)} characters to {file_path}",
                metadata={
                    "file_path": str(path),
                    "bytes_written": written_size,
                    "encoding": encoding,
                    "lines_written": len(content.splitlines()),
                },
            )

        except PermissionError:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Permission denied writing to file: {file_path}",
            )
        except Exception as e:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Unexpected error writing file: {str(e)}",
            )


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List the contents of a directory, showing files and subdirectories."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="dir_path",
                type="string",
                description="Path to the directory to list (default: current directory)",
                required=False,
                default=".",
            ),
            ToolParameter(
                name="show_hidden",
                type="boolean",
                description="Include hidden files/directories (starting with .)",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="show_details",
                type="boolean",
                description="Show file details (size, modification time)",
                required=False,
                default=False,
            ),
        ]

    def execute(
        self, dir_path: str = ".", show_hidden: bool = False, show_details: bool = False
    ) -> ToolResult:
        """Execute directory listing operation."""
        try:
            # Resolve path
            path = pathlib.Path(dir_path).resolve()

            # Check if directory exists and is a directory
            if not path.exists():
                return ToolResult(
                    status=ToolCallStatus.ERROR,
                    error_message=f"Directory does not exist: {dir_path}",
                )

            if not path.is_dir():
                return ToolResult(
                    status=ToolCallStatus.ERROR,
                    error_message=f"Path is not a directory: {dir_path}",
                )

            # List directory contents
            items = []
            for item in path.iterdir():
                # Skip hidden files if not requested
                if not show_hidden and item.name.startswith("."):
                    continue

                if show_details:
                    stat = item.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime
                    import datetime

                    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                    item_type = "DIR" if item.is_dir() else "FILE"
                    size_str = f"{size:>10}" if item.is_file() else "         -"

                    items.append(f"{item_type:<4} {size_str} {mtime_str} {item.name}")
                else:
                    item_type = "📁" if item.is_dir() else "📄"
                    items.append(f"{item_type} {item.name}")

            # Sort items
            items.sort()

            content = (
                f"Contents of {path}:\n" + "\n".join(items)
                if items
                else f"Directory {path} is empty"
            )

            return ToolResult(
                status=ToolCallStatus.SUCCESS,
                content=content,
                metadata={
                    "directory_path": str(path),
                    "item_count": len(items),
                    "show_hidden": show_hidden,
                    "show_details": show_details,
                },
            )

        except PermissionError:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Permission denied accessing directory: {dir_path}",
            )
        except Exception as e:
            return ToolResult(
                status=ToolCallStatus.ERROR,
                error_message=f"Unexpected error listing directory: {str(e)}",
            )


def register_file_tools():
    """Register all file tools with the default registry."""
    default_registry.register(ReadFileTool())
    default_registry.register(WriteFileTool())
    default_registry.register(ListDirectoryTool())


# Auto-register when module is imported
register_file_tools()
