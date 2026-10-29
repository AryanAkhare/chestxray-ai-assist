#!/bin/sh
set -e

# Automatically run checkpoint conversion if converted models are not yet generated
if [ ! -f "/app/data/converted/D/best_model.safetensors" ]; then
    echo "[docker-entrypoint] Converted weights not found in /app/data/converted. Converting checkpoints to safetensors..."
    python /app/scripts/convert_checkpoints.py || echo "[docker-entrypoint] Warning: Checkpoint conversion encountered an error."
fi

# Execute CMD passed to container or default uvicorn
exec "$@"
