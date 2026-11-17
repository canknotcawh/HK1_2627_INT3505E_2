#!/usr/bin/env bash
# Lab 3 — run the Postman collection with Newman and write a JUnit report.
# Starts the Flask API on 127.0.0.1:5000 if it is not already running,
# then stops only the process started here.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${LAB_PORT:-5000}"
BASE_URL="http://127.0.0.1:${PORT}"
mkdir -p reports

API_PID=""
cleanup() {
  if [ -n "$API_PID" ]; then
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if ! curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "Starting API on ${BASE_URL} ..."
  .venv/bin/python -m app --port "${PORT}" > reports/api.log 2>&1 &
  API_PID=$!
  for _ in $(seq 1 50); do
    if curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.2
  done
  if ! curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
    echo "API did not become ready; see reports/api.log" >&2
    exit 1
  fi
fi

npx newman run books-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  -r cli,junit \
  --reporter-junit-export reports/junit.xml | tee reports/newman-cli.txt
