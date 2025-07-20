#!/bin/bash
ssh -L 5000:localhost:5000 eink@einkspotifypizero << EOF
cd eink-spotify-pi/
source venv/bin/activate
python -u eink_flask.py $1
EOF