#!/bin/bash
# Test script for hosted Telegram bot API using curl

BASE_URL="https://telegram-bot-api.royadler.de"
API_KEY="asdfghjkl"

echo "🚀 Testing hosted Telegram bot API"
echo "=================================="
echo "🌐 Target: $BASE_URL"
echo "🔑 API Key: $API_KEY"
echo "=================================="

echo ""
echo "1. Testing basic connectivity..."
echo "   Testing: $BASE_URL/api/health"

# Test health endpoint
HEALTH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL/api/health" 2>/dev/null)
HTTP_STATUS=$(echo $HEALTH_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
HEALTH_BODY=$(echo $HEALTH_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ $HTTP_STATUS -eq 200 ]; then
    echo "   ✅ Health check successful!"
    echo "   📊 Response: $HEALTH_BODY"
else
    echo "   ❌ Health check failed (Status: $HTTP_STATUS)"
    echo "   📄 Response: $HEALTH_BODY"
    echo ""
    echo "💡 Trying alternative endpoints..."
    
    # Try other possible endpoints
    for endpoint in "/health" "/" "/api/" "/api"; do
        echo "   Testing: $BASE_URL$endpoint"
        ALT_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)
        ALT_STATUS=$(echo $ALT_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        ALT_BODY=$(echo $ALT_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')
        
        if [ $ALT_STATUS -eq 200 ]; then
            echo "   ✅ Found working endpoint: $endpoint"
            echo "   📊 Response: $ALT_BODY"
            break
        else
            echo "   ❌ Status: $ALT_STATUS"
        fi
    done
fi

echo ""
echo "2. Testing API endpoints with authentication..."

# Test users endpoint
echo "   Testing: $BASE_URL/api/users"
USERS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    "$BASE_URL/api/users" 2>/dev/null)

USERS_STATUS=$(echo $USERS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
USERS_BODY=$(echo $USERS_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ $USERS_STATUS -eq 200 ]; then
    echo "   ✅ Users endpoint working!"
    echo "   📊 Response: $USERS_BODY"
else
    echo "   ❌ Users endpoint failed (Status: $USERS_STATUS)"
    echo "   📄 Response: $USERS_BODY"
fi

# Test channels endpoint
echo ""
echo "   Testing: $BASE_URL/api/channels"
CHANNELS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    "$BASE_URL/api/channels" 2>/dev/null)

CHANNELS_STATUS=$(echo $CHANNELS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
CHANNELS_BODY=$(echo $CHANNELS_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ $CHANNELS_STATUS -eq 200 ]; then
    echo "   ✅ Channels endpoint working!"
    echo "   📊 Response: $CHANNELS_BODY"
else
    echo "   ❌ Channels endpoint failed (Status: $CHANNELS_STATUS)"
    echo "   📄 Response: $CHANNELS_BODY"
fi

echo ""
echo "3. Testing broadcast functionality..."

# Test broadcast
BROADCAST_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"message": "🧪 Test message from curl"}' \
    "$BASE_URL/api/broadcast" 2>/dev/null)

BROADCAST_STATUS=$(echo $BROADCAST_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
BROADCAST_BODY=$(echo $BROADCAST_RESPONSE | sed -e 's/HTTPSTATUS:.*//g')

if [ $BROADCAST_STATUS -eq 200 ]; then
    echo "   ✅ Broadcast successful!"
    echo "   📊 Response: $BROADCAST_BODY"
else
    echo "   ❌ Broadcast failed (Status: $BROADCAST_STATUS)"
    echo "   📄 Response: $BROADCAST_BODY"
fi

echo ""
echo "=================================="
echo "🏁 Testing completed!"

# Summary
if [ $HTTP_STATUS -eq 200 ] && [ $BROADCAST_STATUS -eq 200 ]; then
    echo "🎉 All tests passed! Your hosted bot API is working correctly!"
else
    echo "❌ Some tests failed. Check the responses above for details."
fi
