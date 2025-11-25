#!/bin/bash
# Quick publish script for Pranthora SDK

set -e  # Exit on error

echo "🚀 Publishing Pranthora SDK to PyPI"

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate llms

# Navigate to SDK directory
cd "$(dirname "$0")"

# Run tests
echo "📋 Running tests..."
python test_sdk.py -v || { echo "❌ Tests failed!"; exit 1; }

# Clean old builds
echo "🧹 Cleaning old builds..."
rm -rf build/ dist/ *.egg-info/

# Build packages
echo "📦 Building packages..."
python -m build || { echo "❌ Build failed!"; exit 1; }

# Ask for PyPI type
read -p "Publish to (test/prod)? " pypi_type

if [ "$pypi_type" = "test" ]; then
    echo "🧪 Uploading to Test PyPI..."
    python -m twine upload --repository testpypi dist/*
elif [ "$pypi_type" = "prod" ]; then
    echo "🚀 Uploading to Production PyPI..."
    read -p "Are you sure you want to publish to PRODUCTION PyPI? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        python -m twine upload dist/*
    else
        echo "❌ Cancelled."
        exit 1
    fi
else
    echo "❌ Invalid choice. Use 'test' or 'prod'"
    exit 1
fi

echo "✅ Done! Check https://pypi.org/project/pranthora/"

