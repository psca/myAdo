import json
import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

def test_get_current_user_id_returns_id():
    from check_prs import get_current_user_id
    mock_profile = {"id": "abc-123-guid", "displayName": "Test User"}
    with patch("check_prs.run_json", return_value=mock_profile):
        result = get_current_user_id()
    assert result == "abc-123-guid"

def test_get_current_user_id_missing_id_exits():
    from check_prs import get_current_user_id
    with patch("check_prs.run_json", return_value={}):
        with pytest.raises(SystemExit) as exc_info:
            get_current_user_id()
    assert exc_info.value.code == 1

def test_get_current_user_id_non_dict_response_exits():
    from check_prs import get_current_user_id
    with patch("check_prs.run_json", return_value=[]):
        with pytest.raises(SystemExit) as exc_info:
            get_current_user_id()
    assert exc_info.value.code == 1
