# Publishing Pranthora SDK to PyPI

This guide will walk you through publishing the Pranthora Python SDK to PyPI so users can install it with `pip install pranthora`.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - **Test PyPI** (for testing): https://test.pypi.org/account/register/
   - **PyPI** (production): https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens for both:
   - Test PyPI: https://test.pypi.org/manage/account/token/
   - Production PyPI: https://pypi.org/manage/account/token/
   - Create a token with scope: "Entire account" or "Project: pranthora"

3. **Required Tools**: Install build tools:
   ```bash
   conda activate llms
   pip install build twine
   ```

## Step-by-Step Publishing Process

### Step 1: Update Version Number

Before publishing, update the version in `setup.py`:

```python
version="1.0.0",  # Change to 1.0.1, 1.1.0, etc.
```

**Versioning Guidelines:**
- `1.0.0` → `1.0.1` (patch: bug fixes)
- `1.0.0` → `1.1.0` (minor: new features, backward compatible)
- `1.0.0` → `2.0.0` (major: breaking changes)

### Step 2: Run Tests

Make sure all tests pass:

```bash
conda activate llms
cd pranthora_sdk
python test_sdk.py -v
```

### Step 3: Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
```

### Step 4: Build Distribution Packages

```bash
# Build source distribution and wheel
python -m build
```

This creates:
- `dist/pranthora-1.0.0.tar.gz` (source distribution)
- `dist/pranthora-1.0.0-py3-none-any.whl` (wheel)

### Step 5: Test on Test PyPI (Recommended)

**First, test on Test PyPI to avoid mistakes:**

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# When prompted:
# Username: __token__
# Password: <your-test-pypi-api-token>
```

**Test Installation:**

```bash
# Create a clean virtual environment to test
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pranthora

# Test the installation
python -c "from pranthora import Pranthora; print('Success!')"
```

### Step 6: Publish to Production PyPI

Once tested, publish to production:

```bash
# Upload to Production PyPI
python -m twine upload dist/*

# When prompted:
# Username: __token__
# Password: <your-production-pypi-api-token>
```

### Step 7: Verify Publication

1. **Check PyPI page**: https://pypi.org/project/pranthora/
2. **Test installation**:
   ```bash
   pip install pranthora
   python -c "from pranthora import Pranthora; print('Installed successfully!')"
   ```

## Complete Publishing Script

Here's a complete script to automate the process:

```bash
#!/bin/bash
# publish.sh

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
    python -m twine upload dist/*
else
    echo "❌ Invalid choice. Use 'test' or 'prod'"
    exit 1
fi

echo "✅ Done! Check https://pypi.org/project/pranthora/"
```

## Configuration Files

### `.pypirc` (Optional - for easier authentication)

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = <your-production-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-test-token>
```

Then you can use:
```bash
twine upload --repository testpypi dist/*
twine upload dist/*  # Uses pypi by default
```

## Updating an Existing Package

To update an existing package:

1. **Increment version** in `setup.py`
2. **Update CHANGELOG.md** (if you have one)
3. **Build and upload**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Troubleshooting

### Error: "File already exists"
- **Solution**: Increment version number in `setup.py`

### Error: "Invalid credentials"
- **Solution**: 
  - Use `__token__` as username
  - Use API token (not password) from PyPI account settings
  - Make sure token has correct scope

### Error: "Package name already taken"
- **Solution**: The package name `pranthora` must be unique. If taken, you'll need to:
  - Use a different name, or
  - Request transfer from current owner

### Error: "Missing required metadata"
- **Solution**: Check `setup.py` has all required fields:
  - `name`
  - `version`
  - `author` or `author_email`
  - `description`

## Best Practices

1. **Always test on Test PyPI first**
2. **Use semantic versioning** (MAJOR.MINOR.PATCH)
3. **Keep a CHANGELOG.md** documenting changes
4. **Tag releases in Git**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
5. **Test installation after publishing**
6. **Update documentation** if API changes

## Quick Reference Commands

```bash
# Activate environment
conda activate llms

# Run tests
python test_sdk.py -v

# Clean and build
rm -rf build/ dist/ *.egg-info/
python -m build

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Upload to Production PyPI
python -m twine upload dist/*

# Install locally for testing
pip install -e .

# Install from PyPI
pip install pranthora

# Install with realtime extras
pip install pranthora[realtime]
```

## Post-Publication Checklist

- [ ] Verify package appears on PyPI
- [ ] Test installation: `pip install pranthora`
- [ ] Test import: `python -c "from pranthora import Pranthora"`
- [ ] Update documentation with installation instructions
- [ ] Create GitHub release (if using GitHub)
- [ ] Announce on social media/docs (optional)

## Support

If you encounter issues:
1. Check PyPI status: https://status.pypi.org/
2. Review PyPI documentation: https://packaging.python.org/
3. Check error messages carefully - they're usually helpful

Happy publishing! 🎉

