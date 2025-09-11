@echo off
echo === Testing Channel-Based API ===
echo.

echo 1. Testing Health Endpoint...
curl -X GET http://localhost:5000/api/health
echo.
echo.

echo 2. Testing Channels Endpoint...
curl -X GET http://localhost:5000/api/channels -H "X-API-Key: asdfghjkl"
echo.
echo.

echo 3. Testing Broadcast to Channel...
curl -X POST http://localhost:5000/api/broadcast-to-channel -H "X-API-Key: asdfghjkl" -H "Content-Type: application/json" -d "{\"message\":\"Test message from batch script!\",\"channel\":\"general\"}"
echo.
echo.

echo 4. Testing Stats Endpoint...
curl -X GET http://localhost:5000/api/stats -H "X-API-Key: asdfghjkl"
echo.
echo.

echo === Testing Complete ===
pause
