---
description: Wrap up current feature — commit, push, merge to main, update main
allowed-tools: Bash(git:*), Bash(gh:*)
---

# Finish Current Feature

Follow these steps in order. Stop and report if any step fails.

1. **Check status**: Run `git status`. If there are uncommitted changes, stage everything and create a commit with a clear conventional commit message based on the diff. If the working tree is clean, skip to step 2.

2. **Push the branch**: Push the current branch to origin. If the remote branch doesn't exist yet, use `--set-upstream`.

3. **Merge to main**: Switch to `main`, pull latest, then merge the feature branch. Use `--no-ff` to preserve the merge commit. If there are merge conflicts, stop and report them — do NOT auto-resolve.

4. **Push main**: Push the updated main to origin.

5. **Clean up**: Delete the local feature branch (the one you just merged).

6. **Summary**: Report what was done — branch name merged, number of commits, and confirm main is up to date.

If any git command fails, stop immediately and explain what went wrong. Never force-push or auto-resolve conflicts.
