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
   uv install -r requirements.txt
   ```

3. **Build Docker container:**

   ```bash
   docker build -t wol-service .
   ```

## Running the Application Locally

1. **Start the FastAPI application locally:**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 25644
   ```

2. **Access the web interface:**

   Open your web browser and navigate to `http://localhost:25644`.

## Docker Setup

1. **Run the Docker container:**

   ```bash
   docker run -d -p 25644:25644 --name wol-service-container wol-service
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
