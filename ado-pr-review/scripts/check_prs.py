#!/usr/bin/env python3
"""
ADO PR Review Script
Lists PRs where current user is a reviewer, checks for active threads,
and optionally approves clean PRs.

Usage:
    python check_prs.py                    # Review only, prompt before approve
    python check_prs.py --auto-approve     # Approve all clean PRs without prompting
    python check_prs.py --project <name>   # Scope to a specific project
    python check_prs.py --repo <name>      # Scope to a specific repository
    python check_prs.py --dry-run          # Report only, no approvals
    python check_prs.py --closed           # Show recently closed/merged PRs summary
"""

import subprocess
import json
import sys
import argparse
import os
import tempfile

def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()

def run_json(cmd):
    out = run(cmd)
    if not out:
        return []
    return json.loads(out)

def get_current_user_id():
    data = run_json("az devops invoke --area profile --resource profiles --route-parameters id=me --api-version 6.0 -o json")
    if not isinstance(data, dict):
        print("ERROR: Could not determine ADO user ID. Run 'az login' and ensure the azure-devops extension is installed.", file=sys.stderr)
        sys.exit(1)
    user_id = data.get("id", "")
    if not user_id:
        print("ERROR: Could not determine ADO user ID. Run 'az login' and ensure the azure-devops extension is installed.", file=sys.stderr)
        sys.exit(1)
    return user_id

def list_my_prs(user_id, project=None, repo=None):
    # No --route-parameters: omitting the repo route uses the org-level endpoint
    # (/_apis/git/pullRequests) which supports cross-project search via searchCriteria.
    cmd = (
        f'az devops invoke '
        f'--area git '
        f'--resource pullRequests '
        f'--query-parameters "searchCriteria.reviewerId={user_id}&searchCriteria.status=active" '
        f'--api-version 7.1 '
        f'-o json'
    )
    data = run_json(cmd)
    prs = data.get("value", []) if isinstance(data, dict) else []

    if project:
        prs = [p for p in prs if p.get("repository", {}).get("project", {}).get("name", "").lower() == project.lower()]
    if repo:
        prs = [p for p in prs if p.get("repository", {}).get("name", "").lower() == repo.lower()]
    return prs

def get_active_threads(pr_id, repo_id, project=None):
    """Use az devops invoke to call the pullRequestThreads REST API."""
    route = f"pullRequestId={pr_id};repositoryId={repo_id}"
    if project:
        route += f";project={project}"
    cmd = (
        f'az devops invoke '
        f'--area git '
        f'--resource pullRequestThreads '
        f'--route-parameters {route} '
        f'--query "value[?status==\'active\']" '
        f'-o json'
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return []

def get_my_vote(pr, user_email):
    reviewers = pr.get("reviewers", [])
    for r in reviewers:
        if r.get("uniqueName", "").lower() == user_email.lower():
            return r.get("vote", 0)
    return 0

def approve_pr(pr, user_id):
    """Approve a PR via the pullRequestReviewers REST API, preserving isRequired."""
    pr_id = pr["pullRequestId"]
    repo_id = pr["repository"]["id"]

    is_required = False
    for r in pr.get("reviewers", []):
        if r.get("id", "") == user_id:
            is_required = r.get("isRequired", False)
            break

    vote_data = json.dumps({"vote": 10, "isRequired": is_required})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(vote_data)
        tmp_path = f.name
    try:
        run(
            f'az devops invoke '
            f'--area git '
            f'--resource pullRequestReviewers '
            f'--route-parameters repositoryId={repo_id} pullRequestId={pr_id} reviewerId={user_id} '
            f'--http-method PUT '
            f'--in-file {tmp_path} '
            f'-o none'
        )
    finally:
        os.unlink(tmp_path)


def list_closed_prs(user_id, project=None, repo=None, top=10):
    cmd = (
        f'az devops invoke '
        f'--area git '
        f'--resource pullRequests '
        f'--query-parameters "searchCriteria.reviewerId={user_id}&searchCriteria.status=completed&$top={top}" '
        f'--api-version 7.1 '
        f'-o json'
    )
    data = run_json(cmd)
    prs = data.get("value", []) if isinstance(data, dict) else []
    if project:
        prs = [p for p in prs if p.get("repository", {}).get("project", {}).get("name", "").lower() == project.lower()]
    if repo:
        prs = [p for p in prs if p.get("repository", {}).get("name", "").lower() == repo.lower()]
    return prs

def vote_label(vote):
    labels = {10: "Approved", 5: "Approved w/suggestions", 0: "No vote", -5: "Waiting for author", -10: "Rejected"}
    return labels.get(vote, f"Vote={vote}")

def main():
    parser = argparse.ArgumentParser(description="Review and approve ADO PRs assigned to me")
    parser.add_argument("--auto-approve", action="store_true", help="Approve all clean PRs without prompting")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no approvals")
    parser.add_argument("--project", help="Filter by project name")
    parser.add_argument("--repo", help="Filter by repository name")
    parser.add_argument("--closed", action="store_true", help="Show recently closed/merged PRs summary")
    args = parser.parse_args()

    print("Fetching current user...")
    user_id = get_current_user_id()
    account = run_json("az account show -o json")
    user_email = account.get("user", {}).get("name", "") if isinstance(account, dict) else ""
    if not user_email:
        print("ERROR: Could not determine account email. Run 'az login'.", file=sys.stderr)
        sys.exit(1)
    print(f"Logged in as: {user_email}\n")

    if args.closed:
        print("Fetching recently closed PRs...")
        closed_prs = list_closed_prs(user_id, project=args.project, repo=args.repo)
        if not closed_prs:
            print("No recently closed PRs found.")
            return
        print(f"Recently closed PRs ({len(closed_prs)}):\n")
        for pr in closed_prs:
            pr_id = pr["pullRequestId"]
            title = pr["title"]
            repo_name = pr["repository"]["name"]
            project_name = pr.get("repository", {}).get("project", {}).get("name", "")
            author = pr.get("createdBy", {}).get("displayName", "Unknown")
            closed_date = (pr.get("closedDate") or pr.get("completionQueueTime") or "")[:10]
            merged_by = pr.get("closedBy", {}).get("displayName", "") if pr.get("closedBy") else ""
            merged_str = f" | Merged by: {merged_by}" if merged_by else ""
            print(f"  ✅ PR #{pr_id} — {title}")
            print(f"     Project: {project_name} | Repo: {repo_name} | Author: {author}{merged_str} | Closed: {closed_date}")
        return

    print("Fetching assigned PRs...")
    prs = list_my_prs(user_id, project=args.project, repo=args.repo)
    if not prs:
        print("No active PRs found where you are a reviewer.")
        return

    print(f"Found {len(prs)} PR(s):\n")

    clean = []
    needs_attention = []

    for pr in prs:
        pr_id = pr["pullRequestId"]
        title = pr["title"]
        repo_id = pr["repository"]["id"]
        repo_name = pr["repository"]["name"]
        author = pr.get("createdBy", {}).get("displayName", "Unknown")
        my_vote = get_my_vote(pr, user_email)

        active_threads = get_active_threads(pr_id, repo_id, project=args.project)

        status_icon = "✅" if not active_threads else "⚠️"
        print(f"{status_icon} PR #{pr_id} — {title}")
        print(f"   Repo: {repo_name} | Author: {author} | Your vote: {vote_label(my_vote)}")

        if active_threads:
            print(f"   Active threads: {len(active_threads)}")
            for t in active_threads[:3]:
                first_comment = t.get("comments", [{}])[0].get("content", "")[:80]
                print(f"     • {first_comment}{'...' if len(first_comment) == 80 else ''}")
            if len(active_threads) > 3:
                print(f"     ... and {len(active_threads) - 3} more")
            needs_attention.append(pr)
        else:
            print(f"   No active threads — clean")
            clean.append(pr)
        print()

    print("=" * 60)
    print(f"Summary: {len(clean)} clean, {len(needs_attention)} need attention\n")

    if not clean:
        print("No clean PRs to approve.")
        return

    if args.dry_run:
        print(f"Dry run — would approve {len(clean)} PR(s): {[p['pullRequestId'] for p in clean]}")
        return

    to_approve = []
    if args.auto_approve:
        to_approve = clean
    else:
        already_approved = [p for p in clean if get_my_vote(p, user_email) == 10]
        not_yet_approved = [p for p in clean if get_my_vote(p, user_email) != 10]

        if already_approved:
            print(f"Already approved by you: {[p['pullRequestId'] for p in already_approved]}")

        if not_yet_approved:
            ids = [p['pullRequestId'] for p in not_yet_approved]
            answer = input(f"\nApprove clean PRs {ids}? [y/N] ").strip().lower()
            if answer == "y":
                to_approve = not_yet_approved

    for pr in to_approve:
        pr_id = pr["pullRequestId"]
        print(f"Approving PR #{pr_id}...")
        approve_pr(pr, user_id)
        print(f"  ✅ Approved PR #{pr_id}")

    if to_approve:
        print(f"\nDone. Approved {len(to_approve)} PR(s).")

if __name__ == "__main__":
    main()
