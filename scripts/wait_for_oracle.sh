#!/usr/bin/env bash
# Wait for Oracle Free container to be ready (up to 120 seconds).
set -euo pipefail

MAX_WAIT=120
INTERVAL=5
elapsed=0

echo "Waiting for Oracle Free to be ready..."
while [ $elapsed -lt $MAX_WAIT ]; do
    if docker compose -f docker/docker-compose.yml exec -T oracle \
        bash -c 'echo "SELECT 1 FROM DUAL;" | sqlplus -S fittrack_app/fittrack_dev_password_change_me@//localhost:1521/FREEPDB1' \
        2>/dev/null | grep -q "^1"; then
        echo "✓ Oracle is ready (${elapsed}s)"
        exit 0
    fi
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
    echo "  Still waiting... (${elapsed}s)"
done

echo "✗ Oracle did not become ready within ${MAX_WAIT}s"
exit 1
