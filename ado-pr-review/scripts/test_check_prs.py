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

def test_list_my_prs_non_dict_response_returns_empty():
    from check_prs import list_my_prs
    with patch("check_prs.run_json", return_value=[]):
        result = list_my_prs("abc-123-guid")
    assert result == []

def test_list_my_prs_filters_by_project_and_repo():
    from check_prs import list_my_prs
    all_prs = {"value": [
        {"pullRequestId": 1, "title": "PR 1", "repository": {"name": "repo1", "project": {"name": "ProjectA"}}},
        {"pullRequestId": 2, "title": "PR 2", "repository": {"name": "repo2", "project": {"name": "ProjectA"}}},
        {"pullRequestId": 3, "title": "PR 3", "repository": {"name": "repo1", "project": {"name": "ProjectB"}}},
    ]}
    with patch("check_prs.run_json", return_value=all_prs):
        result = list_my_prs("abc-123-guid", project="ProjectA", repo="repo1")
    assert len(result) == 1
    assert result[0]["pullRequestId"] == 1


# --- approve_pr ---

def _make_pr(pr_id="99", repo_id="repo-guid", reviewer_id="user-guid", is_required=True):
    return {
        "pullRequestId": pr_id,
        "repository": {"id": repo_id},
        "reviewers": [{"id": reviewer_id, "isRequired": is_required}],
    }

def test_approve_pr_calls_devops_invoke_with_correct_args():
    from check_prs import approve_pr
    pr = _make_pr(pr_id="99", repo_id="repo-guid", reviewer_id="user-guid", is_required=True)
    with patch("check_prs.run") as mock_run, \
         patch("check_prs.tempfile.NamedTemporaryFile") as mock_tmp, \
         patch("check_prs.os.unlink"):
        mock_file = MagicMock()
        mock_file.name = "/tmp/fake.json"
        mock_file.__enter__ = lambda s: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value = mock_file
        approve_pr(pr, "user-guid")
    cmd = mock_run.call_args[0][0]
    assert "pullRequestReviewers" in cmd
    assert "repositoryId=repo-guid" in cmd
    assert "pullRequestId=99" in cmd
    assert "reviewerId=user-guid" in cmd
    assert "--http-method PUT" in cmd

def test_approve_pr_preserves_is_required_true():
    from check_prs import approve_pr
    pr = _make_pr(is_required=True)
    written = {}
    def fake_open(mode, suffix, delete):
        m = MagicMock()
        m.name = "/tmp/fake.json"
        m.__enter__ = lambda s: m
        m.__exit__ = MagicMock(return_value=False)
        m.write = lambda data: written.update({"data": data})
        return m
    with patch("check_prs.run"), \
         patch("check_prs.tempfile.NamedTemporaryFile", side_effect=fake_open), \
         patch("check_prs.os.unlink"):
        approve_pr(pr, "user-guid")
    payload = json.loads(written["data"])
    assert payload["vote"] == 10
    assert payload["isRequired"] is True

def test_approve_pr_preserves_is_required_false():
    from check_prs import approve_pr
    pr = _make_pr(is_required=False)
    written = {}
    def fake_open(mode, suffix, delete):
        m = MagicMock()
        m.name = "/tmp/fake.json"
        m.__enter__ = lambda s: m
        m.__exit__ = MagicMock(return_value=False)
        m.write = lambda data: written.update({"data": data})
        return m
    with patch("check_prs.run"), \
         patch("check_prs.tempfile.NamedTemporaryFile", side_effect=fake_open), \
         patch("check_prs.os.unlink"):
        approve_pr(pr, "user-guid")
    payload = json.loads(written["data"])
    assert payload["isRequired"] is False


# --- list_closed_prs ---

def test_list_closed_prs_returns_completed_prs():
    from check_prs import list_closed_prs
    mock_data = {"value": [
        {"pullRequestId": 10, "repository": {"name": "repo1", "project": {"name": "ProjectA"}}},
        {"pullRequestId": 11, "repository": {"name": "repo2", "project": {"name": "ProjectB"}}},
    ]}
    with patch("check_prs.run_json", return_value=mock_data) as mock_run:
        result = list_closed_prs("user-guid")
    cmd = mock_run.call_args[0][0]
    assert "searchCriteria.status=completed" in cmd
    assert len(result) == 2

def test_list_closed_prs_filters_by_project():
    from check_prs import list_closed_prs
    mock_data = {"value": [
        {"pullRequestId": 10, "repository": {"name": "repo1", "project": {"name": "ProjectA"}}},
        {"pullRequestId": 11, "repository": {"name": "repo2", "project": {"name": "ProjectB"}}},
    ]}
    with patch("check_prs.run_json", return_value=mock_data):
        result = list_closed_prs("user-guid", project="ProjectA")
    assert len(result) == 1
    assert result[0]["pullRequestId"] == 10

def test_list_closed_prs_non_dict_response_returns_empty():
    from check_prs import list_closed_prs
    with patch("check_prs.run_json", return_value=[]):
        result = list_closed_prs("user-guid")
    assert result == []
