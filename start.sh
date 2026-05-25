#!/bin/sh

PORT_VALUE="${PORT:-8000}"

if [ -z "$PORT_VALUE" ] || [ "$PORT_VALUE" = "0" ]; then
  PORT_VALUE=8000
fi

exec uvicorn api:app --host 0.0.0.0 --port "$PORT_VALUE"
