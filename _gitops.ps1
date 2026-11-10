$ErrorActionPreference = "Continue"
$repo = "c:\Users\USER\OneDrive\Desktop\Adrian Codes\SIIMS"
$log = "$repo\_gitops.log"
"=== SIIMS git operations ===" | Out-File $log -Encoding utf8

# 1. Add remote (ignore if exists)
"--- remote ---" | Out-File $log -Append -Encoding utf8
$remotes = git -C $repo remote
if ($remotes -notcontains "origin") {
    git -C $repo remote add origin https://github.com/Aswamas23/SIIMS.git 2>&1 | Out-File $log -Append -Encoding utf8
}
git -C $repo remote -v 2>&1 | Out-File $log -Append -Encoding utf8

# 2. Stage all project files (gitignore excludes node_modules, dist, .env, __pycache__, temp files)
"--- add ---" | Out-File $log -Append -Encoding utf8
git -C $repo add -A 2>&1 | Out-File $log -Append -Encoding utf8
"add exit: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

# 3. Show staged summary
"--- staged count ---" | Out-File $log -Append -Encoding utf8
$staged = git -C $repo diff --cached --name-only
$staged | Out-File $log -Append -Encoding utf8
"staged file count: $($staged.Count)" | Out-File $log -Append -Encoding utf8

# 4. Commit
"--- commit ---" | Out-File $log -Append -Encoding utf8
git -C $repo commit -m "feat: complete SIIMS - frontend, backend, monitoring agent, deployment, docs

- Backend: FastAPI + SQLAlchemy async + Pydantic v2 + Alembic, 17 models,
  15 routers (60+ endpoints), JWT auth, RBAC, alert/licence/notification services,
  APScheduler workers, ReportLab/openpyxl/CSV reports. Python 3.13-compatible deps.
- Frontend: React 18 + TypeScript + Vite + Tailwind + Recharts + TanStack Query,
  14 pages with real API integration (no mock data), builds clean (0 TS errors).
- Monitoring agent: psutil + Windows Registry + service install + SQLite buffer (81 tests pass).
- Deployment: docker-compose (postgres/backend/frontend/nginx), Dockerfiles, nginx config.
- Documentation: architecture, database-design, install, agent, admin, user, troubleshooting guides.
- Security: bcrypt password hashing, JWT, RBAC, audit logging, rate limiting, CORS." 2>&1 | Out-File $log -Append -Encoding utf8
"commit exit: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

# 5. Push
"--- push ---" | Out-File $log -Append -Encoding utf8
git -C $repo push -u origin master 2>&1 | Out-File $log -Append -Encoding utf8
"push exit: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

"=== DONE ===" | Out-File $log -Append -Encoding utf8
