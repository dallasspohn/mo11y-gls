# Persona Images Setup

## How It Works

You can now add images to the sidebar for each persona! Images will be displayed **instead of** the persona description (description moves to an expander).

## Two Ways to Add Images

### Method 1: Specify in Persona JSON (Recommended)

Add an `image_path` field to your persona JSON file:

```json
{
    "name": "Jimmy Spohn",
    "image_path": "media/images/jimmy_spohn.jpg",
    "description": "..."
}
```

The path can be:
- **Relative**: `"media/images/jimmy_spohn.jpg"` (relative to project root)
- **Absolute**: `"/home/dallas/molly-plex/media/images/jimmy_spohn.jpg"`

### Method 2: Default Location (Automatic)

Place images in `media/images/` directory with naming convention:
- `media/images/jimmy_spohn.jpg` (or .png, .webp)
- `media/images/alex_mercer.jpg`
- `media/images/izzy_chan.jpg`

The system will automatically find them based on persona name.

## Image Naming Convention

Convert persona name to lowercase with underscores:
- "Jimmy Spohn" → `media/images/jimmy_spohn.jpg`
- "Alex Mercer" → `media/images/alex_mercer.jpg`
- "Izzy-Chan" → `media/images/izzy_chan.jpg`

Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`

## Example Setup

1. **Create images directory:**
   ```bash
   mkdir images
   ```

2. **Add image for Jim:**
   ```bash
   # Place image at: media/images/jimmy_spohn.jpg
   ```

3. **Optionally specify in cjs.json:**
   ```json
   {
       "name": "Jimmy Spohn",
       "image_path": "media/images/jimmy_spohn.jpg",
       ...
   }
   ```

## How It Displays

- **With image**: Image shown at top of sidebar, description in expander below
- **Without image**: Persona name/title shown, description in expander

## File Structure

```
molly-plex/
├── media/
│   └── images/
│       ├── jimmy_spohn.jpg
│       ├── alex_mercer.jpg
│       └── izzy_chan.jpg
├── sonas/
│   ├── cjs.json (can specify image_path)
│   └── ...
└── app_enhanced.py
```

## Notes

- Images are displayed with `use_container_width=True` (fits sidebar width)
- If image fails to load, falls back to text display
- Description is always available in expander if you want to see it
- Images should be placed in `media/images/` directory
