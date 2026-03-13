---
description: Ship current feature and start the next one — commit, push, merge to main, create new branch
allowed-tools: Bash(git:*), Bash(gh:*)
argument-hint: <next-feature-name>
---

# Ship & Start Next Feature

This command wraps up the current feature and immediately starts the next one.

## Part 1: Finish current feature

1. **Check status**: Run `git status`. If there are uncommitted changes, stage everything and create a commit with a clear conventional commit message based on the diff.

2. **Push the branch**: Push the current branch to origin (`--set-upstream` if needed).

3. **Merge to main**: Switch to `main`, pull latest, merge the feature branch with `--no-ff`. If there are merge conflicts, stop immediately and report them — do NOT auto-resolve.

4. **Push main**: Push updated main to origin.

5. **Clean up**: Delete the merged local feature branch.

## Part 2: Start next feature

6. **Create new branch**: Create and checkout `feat/$ARGUMENTS`. If `$ARGUMENTS` is empty, ask what the next feature should be called before proceeding.

7. **Summary**: Report:
   - Which branch was merged
   - Number of commits shipped
   - The new branch name
   - Confirm everything is clean and ready to go
