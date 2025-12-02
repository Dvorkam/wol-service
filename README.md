# Wakeup on LAN Service

## Project Overview
This is a simple Wakeup on LAN (WoL) service built using FastAPI. It provides a secure HTTP API and a web interface to wake up network devices.

The application is designed to be configured via environment variables and can be run directly as a Python package or as a Docker container.

---

## Quick Start

This section provides a summary for the two most common use cases: running the service as a user and setting up a development environment.

### Option 1: Run as a Standalone Service (User)
This is the simplest way to run the service without cloning the project repository.

1.  **Install the package from PyPI:**
    ```bash
    pip install wol-service
    ```
2.  **Run the service:**
    Pass all required environment variables directly on the command line. This example enables authentication and saves data to a `data` subdirectory.
    ```bash
    # Create a directory for persistent data
    mkdir -p data

    # Run the server
    SECRET_KEY='a-very-strong-and-long-secret-key' \
    ADMIN_USERNAME='admin' \
    ADMIN_PASSWORD='a-good-password' \
    USERS_PATH='./data/users.json' \
    WOL_HOSTS_PATH='./data/hosts.json' \
    uvicorn wol_service.app:app --host 0.0.0.0 --port 25644
    ```
3.  **Access the service** at [http://localhost:25644](http://localhost:25644).

### Option 2: Run for Development (Developer)
This method uses the cloned repository and Docker Compose, which is recommended for development.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/wol-service.git
    cd wol-service
    ```
2.  **Set up your environment:**
    ```bash
    # Create a .env file from the template
    cp .env.in .env
    # Edit .env and set your secrets
    nano .env
    ```
3.  **Start the service:**
    The provided helper script builds the image and starts the development container.
    ```bash
    ./scripts/docker_compose_up.sh
    ```
4.  **Access the service** at [http://localhost:25644](http://localhost:25644).

---

## Detailed Configuration

The application is configured entirely via environment variables.

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

## Advanced Usage and Development

### Docker Compose (Development)
The `docker-compose.yml` file defines multiple services. For local development, you should use the `wol-service-local` service, which mounts your local source code into the container. See the Quick Start section for instructions.

> **Note on Compose Services:** The `docker-compose.yml` also contains a `wol-service` that simulates a production environment by building from `Dockerfile.pypi` and installing the package from a registry. This is useful for testing the packaged version of the application.

### Standalone Docker Image
You can build a Docker image directly from the source code.

1.  **Build the image:**
    ```bash
    ./scripts/docker_build.sh
    ```
2.  **Run the container:**
    This command mounts a local `./data` directory to persist users and hosts and uses an `.env` file for configuration.
    ```bash
    mkdir -p data
    docker run -d -p 25644:25644 --name wol-service-container \
      --env-file .env \
      -e WOL_HOSTS_PATH=/data/hosts.json \
      -e USERS_PATH=/data/users.json \
      -v "$(pwd)/data:/data" \
      wol-service:latest
    ```

### Python (Local Development)
1.  **Install dependencies:**
    Ensure you have `uv` installed (`pip install uv`), then run:
    ```bash
    uv pip install -e '.[dev]'
    ```
2.  **Run the application:**
    This command sources your `.env` file and starts the server with hot-reloading.
    ```bash
    set -a; source .env; set +a
    uvicorn src.wol_service.app:app --reload --host 0.0.0.0 --port 25644
    ```

---

## Testing and Linting
This project uses `pytest` for testing and `ruff` for linting.

*   **Run tests:**
    ```bash
    ./scripts/run_tests.sh
    ```
*   **Run linter:**
    ```bash
    uv run ruff check .
    ```
