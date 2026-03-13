---
description: Start a new feature branch from updated main
allowed-tools: Bash(git:*)
argument-hint: <feature-name>
---

# Start New Feature

Follow these steps in order. Stop and report if any step fails.

1. **Safety check**: Run `git status`. If there are uncommitted changes, stop and warn — do NOT proceed. Suggest running `/done` first.

2. **Update main**: Switch to `main` and pull latest from origin.

3. **Create feature branch**: Create and checkout a new branch named `feat/$ARGUMENTS`. If `$ARGUMENTS` is empty, ask what the feature should be called.

4. **Confirm**: Report the new branch name and that it's based on the latest main.
