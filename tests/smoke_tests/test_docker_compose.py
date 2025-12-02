import subprocess
import time
import httpx
import pytest
import os
import sys


# --- Test Configuration ---
# How long to wait for services to start (in seconds)
STARTUP_WAIT_TIME = 15
# How many times to retry the HTTP request
RETRY_ATTEMPTS = 5
# Delay between retries (in seconds)
RETRY_DELAY = 3
# Base URL for the services
BASE_URL = f"http://localhost:{os.environ.get('PORT', '25644')}"


def run_command(command):
    """Runs a shell command and handles errors."""
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(command)}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        pytest.fail(f"Command failed: {' '.join(command)}", pytrace=False)
    return result


def get_docker_logs(service_name):
    """Prints the logs for a given docker-compose service."""
    print(f"\n--- Logs for service: {service_name} ---")
    log_result = subprocess.run(
        ["docker-compose", "logs", "--no-color", service_name],
        capture_output=True,
        text=True,
    )
    # Prepending each line with service name for clarity in test output
    for line in log_result.stdout.splitlines():
        print(f"[{service_name}] {line}")
    for line in log_result.stderr.splitlines():
        print(f"[{service_name}] {line}", file=sys.stderr)
    print("--- End of logs ---")


@pytest.fixture(scope="function")
def docker_compose_service(request):
    """
    A pytest fixture that manages the lifecycle of a docker-compose service.
    It starts the specified service before a test and tears it down afterward.
    The service name is passed as a parameter from the test function.
    """
    service_name = request.param
    print(f"\n--- Setting up service: {service_name} ---")
    run_command(["docker-compose", "up", "-d", "--build", service_name])

    print(f"Waiting {STARTUP_WAIT_TIME}s for the service to initialize...")
    time.sleep(STARTUP_WAIT_TIME)

    yield service_name  # Pass the service name to the test

    print(f"\n--- Tearing down service: {service_name} ---")
    run_command(["docker-compose", "down", "-v"])


# --- Test Scenarios ---
# Each tuple defines a test case:
# 1. Service name from docker-compose.yml (passed to the fixture)
# 2. URL path to test
# 3. Expected HTTP status code
# 4. Text expected in the response body (case-insensitive)
test_scenarios = [
    (
        "wol-service-local",
        "/login",
        200,
        "login",
    ),
    (
        "wol-service",
        "/login",
        200,
        "login",
    ),
    (
        "wol-service-no-auth",
        "/login",
        200,
        "wake on lan",  # Expect redirect to main page
    ),
]


@pytest.mark.parametrize(
    "docker_compose_service, test_path, expected_status, expected_text",
    test_scenarios,
    indirect=["docker_compose_service"],  # Pass the first parameter to the fixture
)
def test_service_is_accessible(
    docker_compose_service, test_path, expected_status, expected_text
):
    """
    A parametrized test that checks if a given service is accessible and
    responds as expected. It runs for each scenario defined above.
    """
    test_url = f"{BASE_URL}{test_path}"
    print(f"Testing service '{docker_compose_service}' at URL '{test_url}'")

    last_exception = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = httpx.get(test_url, follow_redirects=True)
            response.raise_for_status()

            print(f"Success! Status: {response.status_code}, URL: {response.url}")

            assert response.status_code == expected_status
            assert expected_text in response.text.lower()

            return  # Test passed

        except (httpx.RequestError, httpx.HTTPStatusError, AssertionError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            last_exception = e
            time.sleep(RETRY_DELAY)

    # If all retries fail, print logs and then fail the test
    print(
        f"\nService '{docker_compose_service}' failed checks at {test_url}. Dumping logs:"
    )
    get_docker_logs(docker_compose_service)
    pytest.fail(
        f"Service '{docker_compose_service}' failed checks at {test_url}. "
        f"Last error: {last_exception}",
        pytrace=False,
    )
