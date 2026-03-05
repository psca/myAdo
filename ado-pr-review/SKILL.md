---
name: ado-pr-review
description: Use when the user asks to check, review, or approve their Azure DevOps pull requests. Triggers include "check my PRs", "review my PRs", "approve my PRs", "what PRs do I have", or any request to triage pull requests assigned to them in Azure DevOps. Uses Azure CLI (az repos, az devops invoke) to list assigned PRs, check for active comment threads, and approve clean ones.
---

# ADO PR Review

Automated PR triage and approval for Azure DevOps using the Azure CLI.

## Prerequisites

- `az` CLI installed and logged in (`az login`)
- Azure DevOps extension: `az extension add --name azure-devops`
- Default org/project configured: `az devops configure --defaults organization=https://dev.azure.com/<org> project=<project>`

## Workflow

```
1. Run check_prs.py → lists all active PRs where user is reviewer
2. For each PR → checks active comment threads via REST API
3. Reports: clean (no active threads) vs. needs attention
4. Prompts to approve clean PRs (or --auto-approve to skip prompt)
```

## Quick Start

Run the script directly — it handles everything:

```bash
# Interactive: lists PRs, prompts before approving
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py

# Auto-approve all clean PRs
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --auto-approve

# Scope to a project or repo
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --project "MyProject" --repo "MyRepo"

# Dry run — report only, no approvals
python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --dry-run
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

# Approve a specific PR
az repos pr update --id <PR_ID> --vote approve

# Other vote options: approve, approve-with-suggestions, reset, wait-for-author, reject
```

## Agent Instructions

When the user says "check my PRs" or similar:

1. **Run the script** in dry-run first if unsure: `python ~/.claude/skills/ado-pr-review/scripts/check_prs.py --dry-run`
2. **Show the summary** — how many clean, how many need attention, what threads are blocking
3. **Ask before approving** unless the user said "go ahead and approve" or "auto-approve"
4. **Flag PRs needing attention** — summarize the active thread topics so the user can act on them
5. **Never approve a PR with active threads** — always leave those for the user to resolve

## Troubleshooting

| Issue | Fix |
|---|---|
| `az: command not found` | Install Azure CLI: https://learn.microsoft.com/cli/azure/install-azure-cli |
| `az repos: not found` | `az extension add --name azure-devops` |
| No PRs returned | Check default project: `az devops configure -l` |
| Thread API returns empty | Verify `repositoryId` — use the GUID, not the name |
