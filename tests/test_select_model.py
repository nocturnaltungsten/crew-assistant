
from unittest.mock import patch, Mock

from crew_assistant.select_model import select_model


def test_select_model(monkeypatch):
    fake_response = Mock()
    fake_response.json.return_value = {"data": [{"id": "model-a"}, {"id": "model-b"}]}
    fake_response.raise_for_status.return_value = None
    with patch('crew_assistant.select_model.requests.get', return_value=fake_response):
        with patch('builtins.input', return_value='1'):
            model = select_model()
    assert model == 'model-a'
