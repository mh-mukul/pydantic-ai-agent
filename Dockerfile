FROM python:3.10-slim AS build

# metadata labels
LABEL maintainer="mukulmehedy@gmail.com" \
    version="1.0" \
    description="Chatbot backend"

WORKDIR /app

# 1) Copy and install system deps in one layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    nano \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2) Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# 3) Copy application
COPY . .

# ----------------------------------------------------------

FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy installed Python libs
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
# Copy CLI tools (e.g., alembic, uvicorn, gunicorn)
COPY --from=build /usr/local/bin /usr/local/bin
# Copy application code
COPY --from=build /app /app

# Install tini for process management
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker-entrypoint.sh"]
