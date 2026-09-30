#!/bin/bash
# Start the backend server with proper environment for WeasyPrint on macOS

# Set library path for WeasyPrint (needs Pango/GLib from Homebrew)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -d "/opt/homebrew/lib" ]; then
        export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH}"
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Start the server
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
