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

def test_list_my_prs_org_wide():
    from check_prs import list_my_prs
    mock_prs = {"value": [{"pullRequestId": 1, "title": "PR 1"}]}
    with patch("check_prs.run_json", return_value=mock_prs) as mock_run:
        result = list_my_prs("abc-123-guid")
    call_cmd = mock_run.call_args[0][0]
    assert "searchCriteria.reviewerId=abc-123-guid" in call_cmd
    assert "--project" not in call_cmd
    assert result == mock_prs["value"]

def test_list_my_prs_filters_by_project():
    from check_prs import list_my_prs
    all_prs = {"value": [
        {"pullRequestId": 1, "title": "PR 1", "repository": {"name": "repo1", "project": {"name": "ProjectA"}}},
        {"pullRequestId": 2, "title": "PR 2", "repository": {"name": "repo2", "project": {"name": "ProjectB"}}},
    ]}
    with patch("check_prs.run_json", return_value=all_prs):
        result = list_my_prs("abc-123-guid", project="ProjectA")
    assert len(result) == 1
    assert result[0]["pullRequestId"] == 1

def test_list_my_prs_filters_by_repo():
    from check_prs import list_my_prs
    all_prs = {"value": [
        {"pullRequestId": 1, "title": "PR 1", "repository": {"name": "repo1", "project": {"name": "ProjectA"}}},
        {"pullRequestId": 2, "title": "PR 2", "repository": {"name": "repo2", "project": {"name": "ProjectA"}}},
    ]}
    with patch("check_prs.run_json", return_value=all_prs):
        result = list_my_prs("abc-123-guid", repo="repo1")
    assert len(result) == 1
    assert result[0]["pullRequestId"] == 1
