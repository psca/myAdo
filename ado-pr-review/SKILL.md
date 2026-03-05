---
name: ado-pr-review
description: Use when the user asks to check, review, or approve their Azure DevOps pull requests, or wants to see recently closed/merged PRs. Triggers include "check my PRs", "review my PRs", "approve my PRs", "what PRs do I have", "show closed PRs", or any request to triage pull requests assigned to them in Azure DevOps. Uses az devops invoke to list assigned PRs, check for active comment threads, approve clean ones, and summarise recently merged PRs.
---

# ADO PR Review

Automated PR triage and approval for Azure DevOps using the Azure CLI.

## Prerequisites

- `az` CLI installed and logged in (`az login`)
- Azure DevOps extension: `az extension add --name azure-devops`
- Default org configured: `az devops configure --defaults organization=https://dev.azure.com/<org>`

## Workflow

```
1. Run check_prs.py → lists all active PRs where user is reviewer
2. For each PR → checks active comment threads via REST API
3. Reports: clean (no active threads) vs. needs attention
4. Prompts to approve clean PRs (or --auto-approve to skip prompt)
5. Optionally run with --closed to summarise recently merged PRs
```

## Quick Start

Run the script directly — it handles everything:

```bash
# Interactive: lists PRs, prompts before approving
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py

# Auto-approve all clean PRs
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --auto-approve

# Optional: filter results to a specific project or repo
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --project "MyProject"
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --repo "MyRepo"

# Dry run — report only, no approvals
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --dry-run

# Show recently closed/merged PRs
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --closed
```

## What "Clean" Means

A PR is considered clean (safe to approve) when:
- No active comment threads (status = `active`)
- Build status is not checked by this script — verify separately if required

## Manual CLI Commands

If the script can't run or you need individual operations:

```bash
# List PRs where you're a reviewer
az repos pr list --reviewer "$(az account show --query user.name -o tsv)" --status active -o table

# Check thread status for a specific PR
az devops invoke --area git --resource pullRequestThreads \
  --route-parameters pullRequestId=<ID> repositoryId=<REPO_ID> \
  --query "value[?status=='active']" -o json

# Approve a specific PR (IMPORTANT: preserve isRequired to avoid demoting required reviewers)
# First get your user ID:
MY_ID=$(az devops invoke --area profile --resource profiles --route-parameters id=me --api-version 6.0 --query id -o tsv)
# Then vote (set isRequired based on your current role on the PR):
echo '{"vote": 10, "isRequired": true}' > /tmp/vote.json
az devops invoke \
  --area git --resource pullRequestReviewers \
  --route-parameters repositoryId=<REPO_ID> pullRequestId=<PR_ID> reviewerId=$MY_ID \
  --http-method PUT --in-file /tmp/vote.json -o none
```

## Agent Instructions

When the user says "check my PRs" or similar:

1. **Run the script** in dry-run first if unsure: `python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --dry-run`
2. **Show the summary** — how many clean, how many need attention, what threads are blocking
3. **Ask before approving** unless the user said "go ahead and approve" or "auto-approve"
4. **Flag PRs needing attention** — summarize the active thread topics so the user can act on them
5. **Never approve a PR with active threads** — always leave those for the user to resolve

When the user asks about closed/merged PRs:

1. **Run with --closed**: `python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --closed`
2. **Scope with --project if needed** to narrow results across many projects

## Troubleshooting

| Issue | Fix |
|---|---|
| `az: command not found` | Install Azure CLI: https://learn.microsoft.com/cli/azure/install-azure-cli |
| `az repos: not found` | `az extension add --name azure-devops` |
| No PRs returned | Check default org: `az devops configure -l` and verify `az login` is active |
| Thread API returns empty | Verify `repositoryId` — use the GUID, not the name |
