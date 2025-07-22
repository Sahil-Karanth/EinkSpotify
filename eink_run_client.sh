#!/bin/bash
ssh eink@einkspotifypizero << EOF
cd eink-spotify-pi/
source venv/bin/activate
python -u eink_client.py
sleep 5
EOF