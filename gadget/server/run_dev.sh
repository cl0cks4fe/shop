#!/bin/bash
echo "Starting Gadget Server in Development Mode"
echo "==============================================="

export DEV_MODE=1
export GADGET_PORT=3000
mkdir -p upload transferred

python3 -m venv venv
./venv/bin/pip install -r requirements.txt

cd "$(dirname "$0")"
./venv/bin/python app.py
