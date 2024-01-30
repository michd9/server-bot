#!/bin/bash

echo "Executing tests..."

# Create and activate a disposable virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r ../requirements/requirements-2.txt

# Run the bot script
python bot_test.py

# Deactivate the virtual environment
echo "Test complete, cleaning..."
deactivate
rm -rf .venv    
