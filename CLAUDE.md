# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a personal collection of Claude skills for Azure DevOps automation. Skills are loaded via the `.claude-plugin/marketplace.json` plugin manifest.

## Structure

```
.claude-plugin/marketplace.json   # Plugin manifest — registers skills with Claude
ado-pr-review/                    # Skill: review and approve ADO PRs via Azure CLI
  SKILL.md                        # Skill definition and instructions
  scripts/check_prs.py            # Main automation script
```

## Adding a New Skill

1. Create a directory: `<skill-name>/SKILL.md` + optional `scripts/`, `references/`, `assets/`
2. Register it in `.claude-plugin/marketplace.json` under the `skills` array
3. Use the `example-skills:skill-creator` skill to scaffold: `python3 ~/.claude/plugins/cache/anthropic-agent-skills/example-skills/1ed29a03dc85/skills/skill-creator/scripts/init_skill.py <skill-name> --path .`

## Azure CLI Dependency

All skills in this repo rely on the Azure CLI with the DevOps extension:

```bash
az login
az extension add --name azure-devops
az devops configure --defaults organization=https://dev.azure.com/<org>
```
