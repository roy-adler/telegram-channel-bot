# API Testing Guide

## Comprehensive Test Suite

The repository now includes a consolidated test suite for better organization:

### Python Test Suite
```bash
# Full comprehensive test suite
python tests/test_suite.py

# Quick tests only
python tests/test_suite.py --quick

# Test specific URL/API key
python tests/test_suite.py --url https://your-domain.com --key your_api_key

# Basic API tests
python tests/test_api.py

# Bot stability tests
python tests/test_bot_stability.py
```

## Manual Testing Commands

### PowerShell Commands (if you prefer manual testing):

**1. Health Check:**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET
```

**2. Get Channels:**
```powershell
$headers = @{"X-API-Key" = "asdfghjkl"}
Invoke-RestMethod -Uri "http://localhost:5000/api/channels" -Method GET -Headers $headers
```

**3. Broadcast to Channel:**
```powershell
$headers = @{"X-API-Key" = "asdfghjkl"; "Content-Type" = "application/json"}
$body = @{message = "Test message!"; channel = "general"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/api/broadcast-to-channel" -Method POST -Headers $headers -Body $body
```

**4. Get Stats:**
```powershell
$headers = @{"X-API-Key" = "asdfghjkl"}
Invoke-RestMethod -Uri "http://localhost:5000/api/stats" -Method GET -Headers $headers
```

## Testing Different Environments

### Local Development
```bash
python tests/test_suite.py
```

### Production Server
```bash
python tests/test_suite.py --url https://your-domain.com --key your_production_key
```

## Troubleshooting

- **Container Not Running**: Run `docker-compose up -d` first
- **API Key Issues**: Make sure you're using the correct API key from your environment
- **Import Errors**: Make sure you're running from the project root directory
- **Connection Errors**: Verify the bot is running and accessible at the specified URL

## Test Suite Features

The new `test_suite.py` provides comprehensive testing:

✅ **Connectivity**: Tests basic API connection  
✅ **Authentication**: Verifies API key security  
✅ **Endpoints**: Tests all major API endpoints  
✅ **Broadcasting**: Tests message broadcasting functionality  
✅ **Channel Broadcasting**: Tests channel-specific messages  
✅ **Stability**: Tests API reliability with multiple requests  
✅ **Statistics**: Shows comprehensive bot statistics  

### Available Test Files

All test files are now organized in the `tests/` directory:

- `tests/test_suite.py` - **Main comprehensive test suite** 🌟
- `tests/test_api.py` - Basic API functionality tests
- `tests/test_bot_stability.py` - Bot stability and reliability tests

The consolidated system is much cleaner and more maintainable! 🚀
