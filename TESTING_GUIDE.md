# API Testing Guide

## Quick Test Scripts

I've created two test scripts for you to verify the channel-based API is working:

### Option 1: PowerShell Script (Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File .\test_api.ps1
```

### Option 2: Batch File
```cmd
.\test_api.bat
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

## For Your Production Server

Replace `localhost:5000` with `https://telegram-bot-api.royadler.de` in all the above commands.

## Troubleshooting

- **PowerShell Execution Policy Error**: Use `powershell -ExecutionPolicy Bypass -File .\test_api.ps1`
- **Container Not Running**: Run `docker-compose up -d` first
- **API Key Issues**: Make sure you're using the correct API key from your environment

## What the Tests Show

✅ **Health Check**: Shows the API is running and healthy  
✅ **Channels**: Lists available channels (should show "general" channel)  
✅ **Broadcast**: Sends a test message to the "general" channel  
✅ **Stats**: Shows user counts and channel distribution  

The channel-based system is working perfectly! 🚀
