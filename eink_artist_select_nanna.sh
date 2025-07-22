#!/bin/bash
echo "Starting Flask server with port forwarding..."
echo "Press Ctrl+C to stop the server and cleanup"

# Cleanup function for local processes only
cleanup() {
    echo "Flask server stopped"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup INT TERM

# Single SSH session that handles cleanup AND runs the server
ssh -L 5000:localhost:5000 eink@einkspotifypizero << 'EOF'
# Kill any existing Flask processes first
pkill -f eink_flask.py 2>/dev/null

cd eink-spotify-pi/
source venv/bin/activate
echo "Flask server starting... Press Ctrl+C to stop"

# Set up cleanup trap inside the SSH session
cleanup_remote() {
    echo "Cleaning up on Pi..."
    pkill -f eink_flask.py
    exit 0
}
trap cleanup_remote INT TERM

python -u eink_flask.py nihal
EOF

# This runs when SSH session ends
cleanup