# myAdo

Personal collection of Claude Code skills for Azure DevOps automation.

## Skills

| Skill | Trigger | Description |
|---|---|---|
| `ado-pr-review` | "check my PRs" | Lists PRs assigned to you, checks for active threads, approves clean ones |

## Prerequisites

One-time setup:

```bash
az login --allow-no-subscriptions
az extension add --name azure-devops
az devops configure --defaults organization=https://dev.azure.com/<org> project=<project>
```

`az login --allow-no-subscriptions` is required when your tenant has no Azure subscriptions (DevOps-only tenants). Re-run it when your token expires. The other two commands are permanent.

## Usage

Say "check my PRs" in Claude Code and the `ado-pr-review` skill will handle the rest. Or run the script directly:

```bash
python ado-pr-review/scripts/check_prs.py --dry-run     # Report only
python ado-pr-review/scripts/check_prs.py               # Interactive
python ado-pr-review/scripts/check_prs.py --auto-approve # Approve all clean PRs
```

## Adding Skills

```bash
python3 ~/.claude/plugins/cache/anthropic-agent-skills/example-skills/1ed29a03dc85/skills/skill-creator/scripts/init_skill.py <skill-name> --path .
```

Then register the new skill in `.claude-plugin/marketplace.json`.
