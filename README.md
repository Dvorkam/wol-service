# Wakeup on LAN Service

## Project Overview
This is a simple Wakeup on LAN (WoL) service built using FastAPI. It provides a secure HTTP API and a web interface to wake up network devices.

The application is designed to be configured via environment variables and can be run directly with Python or as a Docker container.

## Configuration
The application is configured entirely via environment variables. For local development with Docker Compose, you can copy the provided template to `.env` and customize it.

1.  **Create a `.env` file:**
    ```bash
    cp .env.in .env
    ```
2.  **Edit `.env`** and fill in your desired `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD`.

### Environment Variables
| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | **Required.** A long, random string used to sign JWT cookies. The app will not start without this. | `None` |
| `ADMIN_USERNAME` | Username for the initial admin account. If empty, authentication is disabled. | `None` |
| `ADMIN_PASSWORD` | Password for the initial admin account. If empty, authentication is disabled. | `None` |
| `USERS_PATH` | Path to the JSON file for storing hashed user records. | `users.json` |
| `WOL_HOSTS_PATH` | Path to the JSON file for storing saved WoL hosts. | `hosts.json` |
| `COOKIE_SECURE` | Set to `true` if running on HTTPS. If `false`, cookies are sent over HTTP. | `false` |
| `COOKIE_SAMESITE` | Cookie SameSite policy. Can be `lax`, `strict`, or `none`. | `lax` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long a login session (JWT token) is valid in minutes. | `30` |

### Authentication Modes
*   **Authenticated (Recommended)**: Set `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
    *   Credentials are hashed and stored in `USERS_PATH` on the first boot.
    *   For security, the credential environment variables are cleared from memory after startup.
    *   CSRF protection is enabled for all state-changing requests.
*   **Unauthenticated (Insecure)**: Leave `ADMIN_USERNAME` and `ADMIN_PASSWORD` unset or empty.
    *   Authentication and CSRF protections are disabled.
    *   This mode is only safe on a strictly trusted private network.

---

## Usage

There are three primary ways to run the service:
1.  **Docker Compose (Recommended for Development)**: Easiest way to get started with a persistent data volume.
2.  **Standalone Docker Image**: For running a specific version or in environments without Compose.
3.  **Directly with Python**: For development without Docker.

### Method 1: Docker Compose (Development)
The `docker-compose.yml` file defines multiple services. For local development, you should use the `wol-service-local` service, which mounts your local source code into the container.

1.  **Set up your environment:**
    ```bash
    # Create a .env file from the template
    cp .env.in .env
    # Edit .env and set your secrets
    nano .env
    ```
2.  **Start the service:**
    The provided helper script builds the image and starts the `wol-service-local` container in the background.
    ```bash
    ./scripts/docker_compose_up.sh
    ```
    Alternatively, you can run the command manually:
    ```bash
    docker compose up --build -d wol-service-local
    ```
3.  **Access the service** at [http://localhost:25644](http://localhost:25644).

> **Note on Compose Services:** The `docker-compose.yml` also contains a `wol-service` that simulates a production environment by building from `Dockerfile.pypi` and installing the package from a registry. This is useful for testing the packaged version of the application.

### Method 2: Standalone Docker Image
You can build a Docker image directly from the source code.

1.  **Build the image:**
    The `docker_build.sh` script is a simple wrapper around the `docker build` command.
    ```bash
    ./scripts/docker_build.sh
    ```
    Or manually:
    ```bash
    docker build -t wol-service:latest .
    ```
2.  **Run the container:**
    This command mounts a local `./data` directory to persist users and hosts.
    ```bash
    # Create data directory if it doesn't exist
    mkdir -p data

    docker run -d -p 25644:25644 --name wol-service-container \
      --env-file .env \
      -e WOL_HOSTS_PATH=/data/hosts.json \
      -e USERS_PATH=/data/users.json \
      -v "$(pwd)/data:/data" \
      wol-service:latest
    ```
    > Note: The `--env-file .env` flag is a convenient way to pass all the variables from your `.env` file.

### Method 3: Directly with Python
1.  **Install dependencies:**
    Ensure you have `uv` installed (`pip install uv`), then run:
    ```bash
    uv pip install -e '.[dev]'
    ```
2.  **Run the application:**
    Load your environment variables and start the server.
    ```bash
    # Make sure your .env file is configured
    set -a; source .env; set +a

    uvicorn src.wol_service.app:app --reload --host 0.0.0.0 --port 25644
    ```

---

## Development & Testing
This project uses `pytest` for testing and `ruff` for linting.

*   **Run tests:**
    The `run_tests.sh` script is a convenient wrapper.
    ```bash
    ./scripts/run_tests.sh
    ```
    Or run `pytest` directly via `uv`:
    ```bash
    uv run pytest
    ```
*   **Run linter:**
    ```bash
    uv run ruff check .
    ```