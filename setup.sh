#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
echo "Welcome. Get started by running: source .venv/bin/activate && aria setup"