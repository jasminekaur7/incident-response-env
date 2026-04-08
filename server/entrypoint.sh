#!/bin/sh
set -e
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7860}"
echo "Starting Incident Response Env on $HOST:$PORT"
exec uvicorn server.app:app --host "$HOST" --port "$PORT" --log-level info