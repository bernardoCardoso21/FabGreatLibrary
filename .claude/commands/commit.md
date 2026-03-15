---
description: Stage and commit all current changes with a conventional commit message
allowed-tools: Bash(git:*)
---

# Commit Current Changes

1. Run `git status` to see what changed.
2. If the working tree is clean, say "Nothing to commit" and stop.
3. Run `git diff --stat` and `git diff --cached --stat` to understand the changes.
4. Stage all changes with `git add -A`.
5. Write a clear conventional commit message based on what actually changed. Use the format: `type(scope): description` (e.g., `feat(auth): add JWT token validation`, `fix(api): handle null response from payments endpoint`).
6. Commit with that message.
7. Report: what was committed (files changed, insertions, deletions) and the commit message used.

Do NOT push. Only commit locally.
