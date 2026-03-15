---
description: Start backend and frontend development servers
allowed-tools: Bash(*)
---

# Start Development Servers

1. **Detect the stack**: Read `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `docker-compose.yml`, and the project's CLAUDE.md to understand what the backend and frontend are and how to start them.

2. **Check for existing processes**: Before starting anything, check if the relevant ports are already in use. If servers are already running, report that and ask if I should restart them.

3. **Start backend first**: Run the backend server in the background. Common patterns:
   - Python: `python manage.py runserver`, `uvicorn`, `flask run`, `fastapi`
   - Node: `npm run dev`, `node server.js`
   - Go: `go run .`
   - Docker: `docker-compose up -d`
   Use whatever is defined in CLAUDE.md or the project's scripts.

4. **Start frontend**: Run the frontend dev server in the background. Common patterns:
   - `npm run dev`, `yarn dev`, `pnpm dev`
   - Check if it's in a subdirectory like `frontend/`, `client/`, `web/`

5. **Verify**: Wait a few seconds, then check that both processes are running and report the URLs (e.g., backend on :8000, frontend on :3000).

6. **Report**: Show both server URLs and confirm they're running.

If CLAUDE.md has specific start commands, always prefer those over guessing.
