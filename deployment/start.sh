#!/bin/bash
# Railway startup script - uses PORT environment variable

PORT=${PORT:-8000}
uvicorn src.api:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 300
