# Use Python 3.12 slim image
FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

# 1. Arguments for flexibility
# INSTALL_TARGET: Can be "." (local) or "wol-service" (PyPI) or "wol-service==0.1.0"
ARG INSTALL_TARGET="wol-service"

ENV UV_SYSTEM_PYTHON=1
ENV HOST=0.0.0.0
ENV PORT=25644

# 2. Copy source code
# We copy this even if we install from PyPI.
# It's cleaner than complex multi-stage logic for a small app.
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# 3. The Hybrid Install
# If INSTALL_TARGET is "wol-service", it downloads from PyPI.
# If INSTALL_TARGET is ".", it installs the files we just copied.
RUN uv pip install --system ${INSTALL_TARGET}

# 4. Runtime
EXPOSE 25644

# Use exec form to ensure signals (SIGTERM) reach python
CMD ["sh", "-c", "exec uvicorn wol_service.app:app --host $HOST --port $PORT"]
