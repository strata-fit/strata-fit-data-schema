#!/usr/bin/env sh
# entrypoint.sh ─ decide what “endpoint” we are supposed to run
set -e

MODE="${RUN_MODE:-algorithm}"
HOST="${API_HOST:-0.0.0.0}"
PORT="${API_PORT:-8000}"

case "$MODE" in
  cli)
    exec strata-fit-validate "$@"
    ;;
  api)
    exec uvicorn api.main:app --host "${HOST}" --port "${PORT}"
    ;;
  algorithm|vantage6)
    exec python -c 'from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()'
    ;;
  *)
    echo "Unknown RUN_MODE '${MODE}'. Use 'cli', 'api', or 'algorithm'." >&2
    exit 1
    ;;
esac
