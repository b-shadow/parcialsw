FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ai-engine/pyproject.toml ./
COPY ai-engine/ai_engine ./ai_engine
COPY ai-engine/README.md ./README.md

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["python", "-m", "ai_engine.inference.health"]
