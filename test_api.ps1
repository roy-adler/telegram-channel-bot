# PowerShell script to test the channel-based API
# Make sure the container is running first: docker-compose up -d

Write-Host "=== Testing Channel-Based API ===" -ForegroundColor Green
Write-Host ""

# Test 1: Health Check
Write-Host "1. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET
    Write-Host "✅ Health Check Success" -ForegroundColor Green
    Write-Host "Response: $($healthResponse | ConvertTo-Json -Depth 3)"
} catch {
    Write-Host "❌ Health Check Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Get Channels
Write-Host "2. Testing Channels Endpoint..." -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = "asdfghjkl"
    }
    $channelsResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/channels" -Method GET -Headers $headers
    Write-Host "✅ Channels Endpoint Success" -ForegroundColor Green
    Write-Host "Response: $($channelsResponse | ConvertTo-Json -Depth 3)"
} catch {
    Write-Host "❌ Channels Endpoint Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Broadcast to Channel
Write-Host "3. Testing Broadcast to Channel..." -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = "asdfghjkl"
        "Content-Type" = "application/json"
    }
    $body = @{
        message = "Test message from PowerShell script!"
        channel = "general"
    } | ConvertTo-Json
    
    $broadcastResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/broadcast-to-channel" -Method POST -Headers $headers -Body $body
    Write-Host "✅ Broadcast Success" -ForegroundColor Green
    Write-Host "Response: $($broadcastResponse | ConvertTo-Json -Depth 3)"
} catch {
    Write-Host "❌ Broadcast Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Get Stats
Write-Host "4. Testing Stats Endpoint..." -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = "asdfghjkl"
    }
    $statsResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/stats" -Method GET -Headers $headers
    Write-Host "✅ Stats Endpoint Success" -ForegroundColor Green
    Write-Host "Response: $($statsResponse | ConvertTo-Json -Depth 3)"
} catch {
    Write-Host "❌ Stats Endpoint Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== Testing Complete ===" -ForegroundColor Green
