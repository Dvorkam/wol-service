# Use Python 3.12 slim image
FROM astral/uv:python3.12-bookworm-slim


# Set working directory
WORKDIR /app

ENV UV_SYSTEM_PYTHON=1
ENV CONTAINER=true

# Copy the pyproject.toml and uv.lock files
COPY pyproject.toml uv.lock README.md ./

# Copy source code
COPY src/ ./src/

# Install dependencies
# Install locked runtime deps to system
# RUN uv export --frozen --no-dev > /tmp/requirements.txt \
# && uv pip install --system -r /tmp/requirements.txt



RUN uv pip install --system .
# Copy tests
COPY tests/ ./tests/

# Copy other files
COPY README.md ./

# Expose port
EXPOSE 25644

# Run the application
CMD ["uvicorn", "wol_service.app:app", "--host", "0.0.0.0", "--port", "25644"]
