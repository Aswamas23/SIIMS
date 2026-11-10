# SIIMS — Troubleshooting

## Backend / API

### `alembic upgrade head` fails with "could not connect to server"
**Cause**: PostgreSQL isn't running, or `DATABASE_URL` is wrong.
**Fix**:
- Confirm PostgreSQL is running: `systemctl status postgresql` (Linux) or check
  Services (Windows).
- Check `DATABASE_URL` in `.env` — the host, port, user, password, and database
  must match your PostgreSQL instance.
- For Docker, use `postgres` as the host (the service name), not `localhost`.

### Login returns 401 "Incorrect email or password"
**Cause**: wrong credentials, or the admin account wasn't seeded.
**Fix**:
- Run the seed script: `python database/seed_data.py` (uses `ADMIN_EMAIL` and
  `ADMIN_PASSWORD` from `.env`).
- Ensure the email is lowercase (the backend lowercases emails on creation).

### JWT errors: "Not enough segments" or "Signature has expired"
**Cause**: malformed or expired token.
**Fix**:
- The frontend auto-refreshes the access token using the refresh token. If the
  refresh token also expired, log in again.
- If errors persist across all users, the `SECRET_KEY` may have changed since
  tokens were issued. Have users log in again.

### CORS error in the browser console
**Cause**: the backend's `FRONTEND_URL` doesn't match where the frontend is served.
**Fix**: set `FRONTEND_URL` in the backend `.env` to the exact origin you use to open
the dashboard (e.g. `http://localhost` or `http://siims.school.edu`), then restart
the backend.

### Rate limit on login
**Cause**: more than 10 login attempts per minute triggers the rate limiter.
**Fix**: wait one minute, or check that no script is hammering the login endpoint.

## Frontend

### Blank page after login
**Cause**: usually a build issue or a missing route.
**Fix**:
- Open the browser dev tools console and check for errors.
- Rebuild the frontend: `cd frontend && npm run build`.
- Ensure the API base URL is correct (`VITE_API_BASE_URL` or the nginx proxy).

### "Cannot find module" during `npm run build`
**Cause**: corrupted `node_modules` (common with OneDrive Files On-Demand).
**Fix**: delete `node_modules` and `package-lock.json`, then `npm install` again.
If on OneDrive, consider moving the project off OneDrive or disabling
Files On-Demand for the project folder.

### Login page loops / redirects repeatedly
**Cause**: the refresh token is present but invalid.
**Fix**: clear localStorage (Application tab in dev tools), then log in fresh.

## Monitoring Agent

### Computer stays "Offline" / "Unknown"
**Cause**: agent not running, wrong server URL, or blocked by firewall.
**Fix**:
- Check the service is running: `services.msc` → SIIMSAgent → Started.
- Verify `server.url` in `config.ini` is reachable from the computer
  (`http://<server-ip>/api`).
- Check the SIIMS backend is up (`/api/v1/health`).
- Confirm the computer's Windows Firewall allows outbound to the server.

### "Authentication failed"
**Cause**: the API key is wrong, expired, or belongs to another computer.
**Fix**: regenerate the agent key in the dashboard (Computers → detail → Generate
Agent Key), update `config.ini`, and restart the service.

### Software inventory is empty
**Cause**: the service can't read the registry, or no software is registered there.
**Fix**: run the service as LocalSystem (the default). Some installers don't write
to the standard Uninstall registry keys; those programs won't appear.

### CPU temperature / SMART show "N/A"
**Cause**: the hardware doesn't expose these values to the OS.
**Fix**: this is expected on many systems — SIIMS reports "unavailable" rather than
inventing a value.

### Agent logs
Located at `%APPDATA%\SIIMSAgent\logs\siims_agent.log`. Set `log_level = DEBUG` in
`config.ini` for detailed output, then restart the service.

## Database

### Migration creates duplicate tables / errors
**Cause**: running `alembic upgrade head` against a DB that was partially created
manually.
**Fix**: drop and recreate the database, then run migrations cleanly:
```bash
dropdb -U siims siims && createdb -U siims siims
cd backend && alembic upgrade head
```

### Dashboard is slow
**Cause**: metrics tables grew beyond retention without pruning.
**Fix**:
- Reduce `data_retention_days` in Settings → Data Retention.
- Manually prune: `DELETE FROM hardware_metrics WHERE recorded_at < now() - interval '30 days';`
- Ensure the `prune_data` scheduler job is running (check backend logs for
  "APScheduler started").

## Reports

### Report download fails / returns an error
**Cause**: `reportlab` or `openpyxl` not installed, or the backend can't render.
**Fix**:
- Confirm both are in `requirements.txt` and installed: `pip install reportlab openpyxl`.
- Check the backend logs for the actual exception.
- Try CSV format first (no external dependencies) to isolate the issue.

### Excel shows all cells as text
**Cause**: numbers are stringified for safe rendering.
**Fix**: this is intentional for cross-format consistency; use Excel's
"Convert to Number" on the column, or use CSV.

## Docker

### `docker-compose up` fails to build backend
**Cause**: port 8000 already in use, or a syntax error in the env file.
**Fix**:
- Stop anything using port 8000 (`netstat -ano | findstr :8000` on Windows).
- Validate `.env` has no trailing spaces or missing values.
- Rebuild: `docker-compose up --build`.

### Containers restart in a loop
**Cause**: backend can't reach postgres (still starting) or env vars missing.
**Fix**:
- The backend depends on postgres being healthy; give it time.
- Check `docker-compose logs backend` for the actual error.
- Ensure `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL` are all set in `.env`.
