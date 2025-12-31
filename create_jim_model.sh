#!/bin/bash
# Script to create Jim's custom model from Modelfile

echo "Creating Jim Spohn model from Modelfile.jim..."
echo ""

# Check if Modelfile exists
if [ ! -f "Modelfile.jim" ]; then
    echo "Error: Modelfile.jim not found!"
    exit 1
fi

# Check if model already exists
if ollama list | grep -q "jim-spohn"; then
    echo "⚠️  Model 'jim-spohn' already exists!"
    echo "Recreating with --force flag..."
    echo "Running: ollama create jim-spohn -f Modelfile.jim --force"
    ollama create jim-spohn -f Modelfile.jim --force
else
    echo "Running: ollama create jim-spohn -f Modelfile.jim"
    ollama create jim-spohn -f Modelfile.jim
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Model 'jim-spohn' created successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Test the model: ollama run jim-spohn 'Tell me about your recent adventures'"
    echo "2. Update sonas/cjs.json: Change model_name from 'phi3:mini' to 'jim-spohn'"
    echo "3. Restart Streamlit: sudo systemctl restart mo11y-streamlit.service"
    echo ""
    echo "To update the model later, run:"
    echo "  ollama create jim-spohn -f Modelfile.jim --force"
else
    echo ""
    echo "❌ Error creating model. Check the output above."
    exit 1
fi
