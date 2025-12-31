# FLUX.1-Krea-dev Image Generation Setup

## Overview
FLUX image generation has been integrated into Mo11y! You can now generate images from text prompts using the Hugging Face Inference API (free tier).

## Setup Instructions

### 1. Install Dependencies
```bash
pip install huggingface-hub
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Get Hugging Face API Token (Optional but Recommended)
1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access is sufficient)
3. Copy the token

**Note**: The free tier works without a token, but you'll have rate limits. A token gives you better rate limits.

### 3. Register the API (Optional)
The API will auto-register when first used, but you can manually register it:

```python
from external_apis import ExternalAPIManager

api_manager = ExternalAPIManager()
api_manager.register_huggingface_image_api(api_token="your_token_here")
```

Or leave `api_token=None` to use the free tier without a token.

## Usage

### In Chat
Simply ask any persona to generate an image:

- "Alex, generate an image of a sunset over mountains"
- "Create a picture of my isekai character"
- "Make an image of a futuristic cityscape"
- "Draw a picture of a cat playing piano"

### Via MCP Tool
The `generate_image` tool is available via MCP:

```python
# Via MCP executor
result = mcp_executor.execute_tool(
    "generate_image",
    {"prompt": "a sunset over mountains"}
)
```

### Direct API Call
```python
from external_apis import ExternalAPIManager

api_manager = ExternalAPIManager()
image_path = api_manager.generate_image(
    prompt="a sunset over mountains",
    width=1024,
    height=1024
)
```

## Features

- **Automatic Detection**: The agent automatically detects when you want to generate an image
- **Image Display**: Generated images appear in the chat interface
- **Download Button**: Download generated images directly from the UI
- **Storage**: Images are saved to `media/images/generated/` directory
- **Naming**: Images are named with timestamp and prompt (sanitized)

## Parameters

- `prompt` (required): Text description of the image
- `style` (optional): Style preset (not currently used by FLUX)
- `negative_prompt` (optional): What to avoid in the image
- `width` (optional): Image width in pixels (default: 1024)
- `height` (optional): Image height in pixels (default: 1024)
- `num_inference_steps` (optional): Denoising steps (default: 28)
- `guidance_scale` (optional): How closely to follow prompt (default: 3.5)

## Example Prompts

- "a beautiful sunset over mountains with clouds"
- "a futuristic cityscape at night with neon lights"
- "a cat playing piano in a cozy room"
- "an isekai adventurer in fantasy armor"
- "a diagram showing financial planning concepts"

## Troubleshooting

### "huggingface_hub not installed"
```bash
pip install huggingface-hub
```

### Rate Limits
- Free tier: Limited requests per hour
- With token: Better rate limits
- Consider using a token for better performance

### Image Generation Fails
- Check internet connection
- Verify Hugging Face API is accessible
- Check that the model name is correct: `black-forest-labs/FLUX.1-Krea-dev`

### Images Not Displaying
- Check that `media/images/generated/` directory exists
- Verify file permissions
- Check that the image file was actually created

## Model Information

- **Model**: FLUX.1-Krea-dev
- **Provider**: Hugging Face Inference API
- **License**: Non-commercial (check terms)
- **Format**: PNG
- **Default Size**: 1024x1024 pixels

## Next Steps

1. Try generating an image: "Alex, generate an image of a sunset"
2. Check the `media/images/generated/` directory for saved images
3. Use generated images in your conversations
4. Share generated images with personas for context

Enjoy generating images! 🎨
