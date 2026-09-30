#!/bin/bash
set -e

echo "=========================================="
echo "Starting Report-OIML Application"
echo "=========================================="

# Configure native libraries for WeasyPrint (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -d "/opt/homebrew/lib" ]; then
        export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH}"
        echo "✓ Configured Homebrew library path for WeasyPrint"
    fi
fi

# Ensure data directory exists (for SQLite database)
if [[ "$DATABASE_URL" == sqlite* ]]; then
    DB_DIR=$(dirname "${DATABASE_URL#sqlite:///}")
    if [ ! -d "$DB_DIR" ]; then
        echo ">> Creating database directory: $DB_DIR"
        mkdir -p "$DB_DIR"
    fi
fi

# Ensure uploads directory exists
if [ -n "$UPLOAD_DIR" ] && [ ! -d "$UPLOAD_DIR" ]; then
    echo ">> Creating uploads directory: $UPLOAD_DIR"
    mkdir -p "$UPLOAD_DIR"
fi

# Run database migrations
echo ">> Running database migrations..."
alembic upgrade head

# Check if database needs seeding (check if users table is empty)
echo ">> Checking database state..."
SEED_CHECK=$(python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from app.core.db import SessionLocal
from app.models import User

db = SessionLocal()
try:
    user_count = db.query(User).count()
    print(user_count)
except:
    print(0)
finally:
    db.close()
")

if [ "$SEED_CHECK" = "0" ]; then
    echo ">> Database is empty, running seed..."
    python seed.py
    echo "✓ Database seeded successfully"
else
    echo "✓ Database already has data ($SEED_CHECK users found)"
fi

echo "=========================================="
echo "Starting uvicorn server..."
echo "=========================================="

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
