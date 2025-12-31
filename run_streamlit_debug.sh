#!/bin/bash
# Run Streamlit with visible console output for debugging
# This allows you to see DEBUG messages in the terminal

cd /home/dallas/mo11y
source /home/dallas/venv/bin/activate

echo "Starting Streamlit in debug mode..."
echo "DEBUG output will be visible in this terminal"
echo "Press Ctrl+C to stop"
echo ""

# Run streamlit with explicit server settings
streamlit run app_enhanced.py \
    --server.headless true \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --logger.level debug
