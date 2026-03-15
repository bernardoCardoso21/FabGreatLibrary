---
description: Update all project .md documentation files to reflect the current state of the codebase
allowed-tools: Bash(find:*), Bash(cat:*), Bash(git:*), Write(*), Read(*)
---

# Update Project Documentation

Scan the entire project and update all markdown documentation to match the current state of the codebase.

## Step 1: Understand the current codebase

- Read the project structure (`find . -type f` excluding node_modules, .git, dist, build, __pycache__, .venv)
- Read key config files (package.json, pyproject.toml, docker-compose.yml, etc.)
- Read the main source files to understand current architecture, models, routes, and utilities
- Run `git log --oneline -20` to see recent changes

## Step 2: Find all .md files

- Run `find . -name "*.md" -not -path "./.git/*" -not -path "*/node_modules/*"` to list every markdown file in the project

## Step 3: Update each file

For each .md file found, read it and update it to reflect the current reality:

- **CLAUDE.md** (root): Update project overview, tech stack, architecture, build/test/lint commands, file organization, coding conventions. This is the most important file — be thorough.
- **README.md**: Update project description, setup instructions, available scripts, API endpoints, environment variables, and usage examples. Make sure installation steps actually work with the current dependencies.
- **Nested CLAUDE.md files**: Update module-specific context to match current code in that directory.
- **Any other .md files** (CONTRIBUTING.md, API.md, CHANGELOG.md, etc.): Update to match current state.

## Rules

- Only update content that is **actually outdated or missing**. Don't rewrite sections that are already accurate.
- Preserve the existing structure and style of each file. Don't reorganize unless it's clearly broken.
- If a .md file references files, functions, or endpoints that no longer exist, remove or update those references.
- If new modules, routes, models, or features exist that aren't documented, add them.
- After updating, run `git diff --stat` and report what changed across all files.
