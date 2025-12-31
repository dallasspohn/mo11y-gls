# Free Image Generation Setup

## ✅ Updated to Use Free Model

The image generation has been updated to use **FREE Stable Diffusion** instead of the paid FLUX.1-Krea-dev model.

### Model Used
- **runwayml/stable-diffusion-v1-5** - Completely free, no payment required
- Works with Hugging Face Inference API free tier
- Good quality image generation

### How It Works

1. **No API Token Required** (but recommended for higher rate limits)
   - Works without token (anonymous access)
   - With free token: higher rate limits
   - Get free token at: https://huggingface.co/settings/tokens

2. **Rate Limits**
   - Without token: ~30 requests/hour
   - With free token: ~1000 requests/day
   - More than enough for personal use!

### Testing

Ask Alex: "Generate an image of a sunset"

The system will:
1. Use free Stable Diffusion model
2. Generate image (may take 10-30 seconds)
3. Save to `media/images/generated/`
4. Display in chat

### Alternative Free Options

If you want even better quality or different models:

1. **Other Free Hugging Face Models:**
   - `stabilityai/stable-diffusion-2-1` (alternative)
   - `CompVis/stable-diffusion-v1-4` (older but still good)

2. **Local Generation (if you have GPU):**
   - Install Ollama image models (requires GPU)
   - Use local Stable Diffusion

### Current Configuration

The code now defaults to `runwayml/stable-diffusion-v1-5` which is:
- ✅ Free
- ✅ No payment required
- ✅ Good quality
- ✅ Works immediately

No changes needed - just restart Streamlit and try it!
