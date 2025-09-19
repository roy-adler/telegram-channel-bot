# Test Suite

This directory contains all Python test files for the Telegram Bot API.

## Test Files

### `test_suite.py` - Main Test Suite 🌟
Comprehensive test suite with all functionality:
```bash
# Full test suite
python tests/test_suite.py

# Quick tests only  
python tests/test_suite.py --quick

# Custom URL/API key
python tests/test_suite.py --url https://your-domain.com --key your_api_key
```

### `test_api.py` - Basic API Tests
Simple API functionality tests:
```bash
python tests/test_api.py
```

### `test_bot_stability.py` - Stability Tests  
Bot stability and reliability tests:
```bash
python tests/test_bot_stability.py
```

## Running Tests

**From project root directory:**
```bash
# Recommended - comprehensive test suite
python tests/test_suite.py

# Quick smoke tests
python tests/test_suite.py --quick
```

## Test Features

- ✅ API connectivity testing
- ✅ Authentication verification
- ✅ Endpoint functionality testing
- ✅ Broadcasting functionality
- ✅ Channel-specific broadcasting
- ✅ Stability and reliability testing
- ✅ Comprehensive error handling
- ✅ Statistics and reporting

All tests are designed to work with both local development and production environments.
