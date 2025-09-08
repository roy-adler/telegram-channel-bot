# syntax=docker/dockerfile:1.7
ARG PY_VERSION=3.12
FROM python:${PY_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# ---- deps layer (only invalidates when requirements.txt changes)
FROM base AS deps
RUN --mount=type=cache,target=/root/.cache/pip apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install --no-input -r requirements.txt

# ---- runtime (copy venv/site-packages from deps; then app code)
FROM base AS runtime
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# app code LAST → tiny rebuild on change
COPY . .
EXPOSE 8080
USER 1000:1000
CMD ["python", "bot.py"]
