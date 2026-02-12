#!/bin/bash
set -e

echo "Building Intranet Frontend Package..."

# 1. Build React App
echo "Building React App..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build
cd ..

# 2. Generate NC Package
echo "Generating NC Package (demo.zip)..."
python3 build_intranet_frontend.py

echo "Done! demo.zip is ready."
