# Use Python 3.12 slim image
FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1
ENV HOST=0.0.0.0
ENV PORT=25644

# Copy project and source files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install the project in editable mode, including test dependencies.
# This is the standard for development environments. It ensures that the
# running code is always the code from the source directory.
RUN uv pip install --system -e .

# Runtime
EXPOSE 25644

# Use exec form to ensure signals (SIGTERM) reach python
CMD ["sh", "-c", "exec uvicorn wol_service.app:app --host $HOST --port $PORT"]
