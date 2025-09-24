#!/bin/bash
export DEV_MODE=1
export GADGET_PORT=3000
mkdir -p gadget/server/upload gadget/server/transferred

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r gadget/server/requirements.txt

cd gadget/server
python app.py
