# FLUX.1-Krea-dev Integration Plan

## Overview
FLUX.1-Krea-dev is a text-to-image generation model that can be integrated into the Mo11y app to allow personas to generate images on demand.

## Model Details
- **Type**: Text-to-Image (Diffusion Model)
- **Library**: Diffusers (FluxPipeline)
- **Providers**: Hugging Face, Replicate, fal.ai
- **License**: Non-commercial (check terms)

## Integration Options

### Option 1: Hugging Face Inference API (Recommended for Testing)
- **Pros**: Easy to set up, free tier available
- **Cons**: Rate limits, requires API key
- **Setup**: 
  ```python
  from huggingface_hub import InferenceClient
  client = InferenceClient(token="your_token")
  image = client.text_to_image("prompt")
  ```

### Option 2: Replicate API
- **Pros**: Reliable, good performance
- **Cons**: Pay-per-use pricing
- **Setup**:
  ```python
  import replicate
  output = replicate.run(
      "black-forest-labs/flux-krea-dev",
      input={"prompt": "your prompt"}
  )
  ```

### Option 3: fal.ai API
- **Pros**: Fast, good for production
- **Cons**: Requires API key, pricing
- **Setup**:
  ```python
  import fal_client
  result = fal_client.subscribe("fal-ai/flux/krea", arguments={"prompt": "your prompt"})
  ```

### Option 4: Local Installation (Advanced)
- **Pros**: No API costs, full control
- **Cons**: Requires GPU, large model size (~24GB), complex setup
- **Setup**: Install diffusers library and load model locally

## Recommended Implementation

### Step 1: Add Image Generation to External APIs
Create a new method in `external_apis.py`:
```python
def generate_image(self, prompt: str, style: str = "default") -> Optional[str]:
    """Generate image using FLUX.1-Krea-dev"""
    # Implementation using chosen provider
    # Returns path to saved image or None
```

### Step 2: Add MCP Tool (Optional)
Create an MCP tool that wraps the image generation:
- Tool name: `generate_image`
- Parameters: `prompt`, `style` (optional)
- Returns: Image file path or URL

### Step 3: Update Personas
Add image generation capability to personas:
- Alex: "I can create images for you if you'd like"
- Jim: Could generate images of his isekai adventures
- Tool Builder: Generate diagrams/documentation images

### Step 4: Streamlit UI Integration
Add image display in `app_enhanced.py`:
- Show generated images in chat
- Allow saving/downloading
- Store in `media/images/generated/` directory

## Usage Examples

### For Users:
- "Alex, generate an image of a sunset over mountains"
- "Create a picture of my isekai character"
- "Make a diagram showing my financial plan"

### For Personas:
- Alex could proactively suggest: "Would you like me to create a visual for your financial goals?"
- Jim could describe his adventures and generate images
- Tool Builder could generate architecture diagrams

## Considerations

1. **License**: FLUX.1-Krea-dev has a non-commercial license - verify your use case
2. **Costs**: API calls cost money (except free tiers)
3. **Performance**: Image generation takes 5-30 seconds typically
4. **Storage**: Generated images need storage space
5. **Moderation**: May want to filter inappropriate prompts

## Next Steps

1. Choose integration method (recommend Hugging Face API for testing)
2. Add image generation method to `external_apis.py`
3. Create MCP tool wrapper (optional)
4. Update agent to detect image generation requests
5. Add UI support in Streamlit
6. Test with personas

## Code Structure

```
external_apis.py
  └── ExternalAPIManager
      └── generate_image(prompt, style) -> str (image path)

mcp_tools/
  └── image_generator.py (optional)
      └── generate_image_tool

app_enhanced.py
  └── Display generated images in chat
  └── Save to media/images/generated/
```
