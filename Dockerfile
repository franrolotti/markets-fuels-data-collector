FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --upgrade pip && pip install -e .
COPY . /app