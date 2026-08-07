#!/usr/bin/env bash
# Build script for Render.com

set -o errexit  # Exit on error

echo "📦 Installing dependencies..."

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "🗄️ Setting up database..."

# Initialize database
python -c "
import sys
sys.path.insert(0, 'backend')
from database import init_db
init_db()
print('✅ Database initialized')
"

echo "🔄 Running migrations..."

# Run migration for superadmin field
python migrate_add_superadmin.py || true

echo "✅ Build complete!"
