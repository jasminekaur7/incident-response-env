FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 envuser

WORKDIR /app/env

COPY server/requirements.txt /app/env/server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY . /app/env/

RUN chmod +x /app/env/server/entrypoint.sh

ENV PYTHONPATH=/app/env:/app
ENV PORT=7860
ENV HOST=0.0.0.0

RUN chown -R envuser:envuser /app
USER envuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["/app/env/server/entrypoint.sh"]