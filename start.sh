#!/bin/sh

PORT_VALUE="${PORT:-8000}"

if [ -z "$PORT_VALUE" ] || [ "$PORT_VALUE" = "0" ] || [ "$PORT_VALUE" = '$PORT' ]; then
  PORT_VALUE=8000
fi

case "$PORT_VALUE" in
  ''|*[!0-9]*)
    echo "Invalid PORT value '$PORT_VALUE', defaulting to 8000"
    PORT_VALUE=8000
    ;;
  *)
    ;;
esac

exec uvicorn api:app --host 0.0.0.0 --port "$PORT_VALUE"
