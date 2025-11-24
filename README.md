# Wakeup on LAN Service

## Project Overview

This is a simple Wakeup on LAN (WoL) service built using FastAPI and Python. It provides an HTTP API to wake up network devices over the local area network.

## Requirements

- Docker
- Python 3.9+
- uvicorn[standard]
- jinja2
- argon2
- pytest (for testing)
- httpx (for testing)

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-repo/wol-service.git
   cd wol-service
   ```

2. **Install dependencies using uv:**

   First, ensure you have `uv` installed. If not, you can install it via pip:

   ```bash
   pip install uv
   ```

   Then, run the following command to install all necessary Python dependencies:

   ```bash
   uv install -e .
   ```

3. **Build Docker container:**

   ```bash
   docker build -t wol-service .
   ```

## Default Admin Account

The service can be configured with a default admin account using environment variables (recommended):

- `ADMIN_USERNAME`: Username for the default admin account
- `ADMIN_PASSWORD`: Password for the default admin account
- `SECRET_KEY` **(required)**: Used to sign JWT cookies. The app refuses to start without it.
- `USERS_PATH` (default: `users.json`): Location where hashed user records are stored. Admin credentials from the environment are written here on first boot.
- `WOL_HOSTS_PATH` (default: `hosts.json`): Location for saved hosts.
- `COOKIE_SECURE` (default: `true`): Set to `false` for HTTP-only local testing so cookies are sent without TLS.
- `COOKIE_SAMESITE` (default: `lax`): Adjust only if your deployment requires it.

The default admin account is created during application startup and the environment variables are automatically removed for security reasons. This is useful for initial setup in containerized environments.

*Note: For security reasons, the ADMIN_USERNAME and ADMIN_PASSWORD environment variables are automatically removed from the environment after creating the default admin account.*
*The application will fail fast if `SECRET_KEY` is missing so tokens cannot be forged.*

If you choose to run **without** `ADMIN_USERNAME`/`ADMIN_PASSWORD`, authentication and CSRF protections are disabled and all endpoints become open. A warning is logged to remind you this mode is unsafe for shared networks.
If you explicitly set both to empty strings (e.g., `ADMIN_USERNAME= ADMIN_PASSWORD=`) any persisted users are ignored and the app runs unauthenticated for that process only.

### CSRF protection

Login issues an `access_token` (HTTP-only) and a `csrf_token` (readable by the browser). All state-changing requests (`/wake`, `/api/hosts` POST/DELETE) must include the CSRF token via a hidden form field or `X-CSRF-Token` header; the UI pages do this automatically.
When authentication is disabled, `/login` redirects to `/wake`, and the wake/host endpoints are open (but this is unsafe outside a trusted LAN).
## Running the Application Locally

1. **Start the FastAPI application locally (remember a SECRET_KEY and credentials are required):**

   ```bash
   SECRET_KEY=change-me \
   ADMIN_USERNAME=admin \
   ADMIN_PASSWORD=adminpass \
   uv run uvicorn wol_service.app:app --reload --host 0.0.0.0 --port 25644
   ```

2. **Access the web interface:**

   Open your web browser and navigate to `http://localhost:25644`.

## Docker Setup

1. **Run the Docker container:**

   ```bash
   mkdir -p data
   docker run -d -p 25644:25644 --name wol-service-container \
     -e SECRET_KEY=change-me \
     -e ADMIN_USERNAME=admin \
     -e ADMIN_PASSWORD=adminpass \
     -e WOL_HOSTS_PATH=/data/hosts.json \
     -e USERS_PATH=/data/users.json \
     -v "$(pwd)/data:/data" \
     wol-service
   ```

2. **Access the web interface:**

   Open your web browser and navigate to `http://localhost:25644`.

## GitHub Actions Configuration

This project uses GitHub Actions for continuous integration and deployment:

- **Unit Tests:** Automatically run tests using pytest.
- **Versioning:** Manages version tags for releases.
- **Release Handling:** Automates the release process.

*Note: No additional GitHub Actions configurations are included in this initial setup.*

## Contributing Guidelines

1. Fork the repository and create your branch from `main`.
2. Create a new branch for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes and commit them:

   ```bash
   git commit -m "Add some feature"
   ```

4. Push to the branch:

   ```bash
   git push origin feature/your-feature-name
   ```

5. Open a pull request in GitHub.

## Testing

Run the suite (using the existing `.venv`) with uv:

```bash
UV_CACHE_DIR=.uv-cache uv run --no-sync pytest
```

Helper scripts:

- `scripts/run_tests.sh` — runs the test suite via uv.
- `scripts/docker_build.sh` — builds a local Docker image (set `IMAGE_TAG` to override the tag).
- `scripts/docker_compose_up.sh` — wrapper for `docker compose up --build` (compose mounts `./data` to persist hosts/users).
