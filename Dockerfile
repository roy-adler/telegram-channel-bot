# syntax=docker/dockerfile:1.7
ARG PY_VERSION=3.12
FROM python:${PY_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# ---- deps layer (rebuilds only when requirements.txt changes)
FROM base AS deps
# (no extra apt packages needed; keep cache mount for pip)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip \
 && pip install --no-input -r requirements.txt

# ---- runtime
FROM base AS runtime
ARG PY_VERSION
# copy installed deps from deps stage
COPY --from=deps /usr/local/lib/python${PY_VERSION}/site-packages /usr/local/lib/python${PY_VERSION}/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# app code LAST → tiny rebuild on change
COPY . .

# Create a directory for the database and set permissions
RUN mkdir -p /app/data && chown -R 1000:1000 /app/data && chmod -R 755 /app/data

EXPOSE 5000
USER 1000:1000
CMD ["python", "bot.py"]
