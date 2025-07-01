"""Unit tests for model selector utility."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.crew_assistant.utils.model_selector import select_model


class TestModelSelector:
    """Test the model selector utility."""

    def test_successful_model_selection(self, mock_requests):
        """Test successful model selection."""
        with patch("builtins.input", return_value="1"):
            result = select_model()

        assert result == "test-model-1"
        assert "OPENAI_API_MODEL" in patch.dict("os.environ")

    def test_model_selection_with_second_option(self, mock_requests):
        """Test selecting the second model option."""
        with patch("builtins.input", return_value="2"):
            result = select_model()

        assert result == "test-model-2"

    def test_invalid_selection(self, mock_requests):
        """Test invalid selection input."""
        with patch("builtins.input", return_value="invalid"):
            result = select_model()

        assert result is None

    def test_out_of_range_selection(self, mock_requests):
        """Test out of range selection."""
        with patch("builtins.input", return_value="99"):
            with pytest.raises(IndexError):
                select_model()

    def test_no_models_available(self):
        """Test when no models are available."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response):
            result = select_model()

        assert result is None

    def test_api_error(self):
        """Test when API returns an error."""
        with patch("requests.get", side_effect=requests.RequestException("API Error")):
            result = select_model()

        assert result is None

    def test_environment_variable_set(self, mock_requests):
        """Test that environment variable is properly set."""
        with patch("builtins.input", return_value="1"), patch.dict("os.environ", {}, clear=True):
            import os

            result = select_model()

            assert result == "test-model-1"
            assert os.environ.get("OPENAI_API_MODEL") == "test-model-1"
