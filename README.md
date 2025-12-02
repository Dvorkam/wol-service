# Wakeup on LAN Service
## Project Overview
This is a simple Wakeup on LAN (WoL) service built using FastAPI. It provides an HTTP API and a web interface to wake up network devices over the local area network.
## Requirements
You can run this application using Python directly or via Docker.
 * Option A: Python 3.10+ (managed via uv)
 * Option B: Docker Engine (Available at [github repo](https://github.com/Dvorkam/wol-service/releases))
 * Option C: Docker Compose (Available at [github repo](https://github.com/Dvorkam/wol-service/releases))
## Configuration
The application is configured via environment variables. These apply regardless of the running method chosen.
### Environment Variables
| Variable | Description | Default |
|---|---|---|
| SECRET_KEY | Required. Used to sign JWT cookies. The app will not start without this. | None |
| ADMIN_USERNAME | Username for the initial admin account. If empty, authentication is disabled. | None |
| ADMIN_PASSWORD | Password for the initial admin account. If empty, authentication is disabled. | None |
| USERS_PATH | Path to store hashed user records. | users.json |
| WOL_HOSTS_PATH | Path to store saved WoL hosts. | hosts.json |
| COOKIE_SECURE | Set to `true` if running on HTTPS. If `false`, cookies are sent over HTTP. | `false` |
| COOKIE_SAMESITE | Cookie SameSite policy. Can be `lax`, `strict`, or `none`. | `lax` |
| ACCESS_TOKEN_EXPIRE_MINUTES | How long a login session (JWT token) is valid in minutes. | `30` |
| LOG_LEVEL | Logging level for the application. | `INFO` |
| TOKEN_ISSUER | JWT token issuer string. | `wol-service` |
| TOKEN_AUDIENCE | JWT token audience string. | `wol-service-users` |
### Authentication Modes
 * Authenticated (Recommended): Set ADMIN_USERNAME and ADMIN_PASSWORD.
   * Credentials are hashed and stored in USERS_PATH on the first boot.
   * Environment variables for credentials are cleared from memory immediately after startup.
   * CSRF protection is enabled.
 * Unauthenticated (Insecure): Leave ADMIN_USERNAME and ADMIN_PASSWORD unset (or set to empty strings).
   * Authentication and CSRF protections are disabled.
   * All endpoints are open. Only use this on a strictly trusted LAN.
## Usage Method 1: Python (Local)
Use this method to run the application directly on the host machine.
 * Install dependencies:
   Ensure you have uv installed (pip install uv), then install project dependencies:
```bash
   uv install -e .
dependencies:
```

 * Run the application:
   Replace the values below as needed.

```bash
   SECRET_KEY=change-me-to-something-secure \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=adminpass \
COOKIE_SECURE=false \
uv run uvicorn wol_service.app:app --reload --host 0.0.0.0 --port 25644
```
 * Access: Open http://localhost:25644.
Usage Method 2: Docker (Standalone)
 * Build the image:
```bash
   docker build -t wol-service .
```

 * Run the container:
   This command mounts a local ./data directory to persist users and hosts.
```bash
mkdir -p data

docker run -d -p 25644:25644 --name wol-service-container \
  -e SECRET_KEY=change-me-to-something-secure \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=adminpass \
  -e COOKIE_SECURE=false \
  -e WOL_HOSTS_PATH=/data/hosts.json \
  -e USERS_PATH=/data/users.json \
  -v "$(pwd)/data:/data" \
  wol-service
```
 * Access: Open http://localhost:25644.
Usage Method 3: Docker Compose
If you prefer using Compose, you can use the provided helper script or run standard compose commands.
 * Start the service:
   # Using the helper script (builds and mounts ./data automatically)
```bash
./scripts/docker_compose_up.sh
```

# OR using standard docker compose (ensure your compose file maps volumes correctly)
```bash
docker compose up --build -d
```

Development & Testing
This project uses pytest. To run the test suite:
```bash
uv run --no-sync pytest
```
> Note: A helper script is also available at scripts/run_tests.sh.
>
Security Notes
 * Production Deployment: Always use a strong, random SECRET_KEY.
 * Persistence: Ensure users.json and hosts.json are stored on a persistent volume (as shown in the Docker example), or data will be lost on container restart.
 * HTTPS: If running behind a reverse proxy with HTTPS, remove COOKIE_SECURE=false (let it default to true).
