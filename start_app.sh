#!/bin/bash
cd /home/$USER/sync-kommo
source venv/bin/activate
export FLASK_ENV=production
export FLASK_PORT=5000
python3 src/main.py
