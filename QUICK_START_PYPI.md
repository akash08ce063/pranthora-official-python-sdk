# Quick Start: Publishing to PyPI

## 🚀 Fast Track (5 minutes)

### 1. Install Build Tools
```bash
conda activate llms
pip install build twine
```

### 2. Create PyPI Accounts
- **Test PyPI**: https://test.pypi.org/account/register/
- **Production PyPI**: https://pypi.org/account/register/
- **Get API tokens** from account settings

### 3. Build & Publish

**Test first:**
```bash
cd pranthora_sdk
python -m build
python -m twine upload --repository testpypi dist/*
# Username: __token__
# Password: <your-test-token>
```

**Then production:**
```bash
python -m twine upload dist/*
# Username: __token__
# Password: <your-production-token>
```

### 4. Verify
```bash
pip install pranthora
python -c "from pranthora import Pranthora; print('✅ Success!')"
```

## 📋 Or Use the Script

```bash
./publish.sh
# Choose 'test' first, then 'prod'
```

## 📚 Full Guide

See [PYPI_PUBLISHING.md](PYPI_PUBLISHING.md) for detailed instructions.

