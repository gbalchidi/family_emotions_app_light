#!/bin/bash

# Start shadowsocks client in background
echo "Starting shadowsocks client..."
ss-local -s 35.204.105.5 -p 23415 -b 127.0.0.1 -l 1080 -k "p1zsciXdqxcIJWqKvIb4TC" -m chacha20-ietf-poly1305 &
SS_PID=$!

# Wait for proxy to start
sleep 5

# Set environment to use local proxy
export USE_PROXY=true
export PROXY_URL=socks5://127.0.0.1:1080

# Start the bot
echo "Starting bot..."
python -m src.main

# Cleanup on exit
trap "kill $SS_PID" EXIT