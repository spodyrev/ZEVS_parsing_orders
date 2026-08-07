#!/usr/bin/env bash
# Build script for Render.com

set -o errexit  # Exit on error

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "
import sys
sys.path.insert(0, 'backend')
from database import init_db
init_db()
print('✅ Database initialized')
"

echo "✅ Build complete!"
