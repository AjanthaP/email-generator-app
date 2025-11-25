# Icon Assets

The extension icons are currently placeholders. For production, you should:

## Option 1: Use the SVG Template
Convert `icon.svg` to PNG at required sizes (16x16, 48x48, 128x128) using:
- Online tools: CloudConvert, Convertio, or similar
- Design software: Figma, Adobe Illustrator, Inkscape
- Command line: ImageMagick or similar

```bash
# Example with ImageMagick (if installed)
magick icon.svg -resize 16x16 icon-16.png
magick icon.svg -resize 48x48 icon-48.png
magick icon.svg -resize 128x128 icon-128.png
```

## Option 2: Design Custom Icons
Use design tools to create professional icons:
- **Figma** (free): Export at 1x, 2x, 3x for different sizes
- **Canva** (free): Use icon templates and export
- **Adobe Illustrator**: Professional vector editing
- **Inkscape** (free): Open-source vector editor

## Option 3: AI-Generated Icons
Use AI tools to generate custom icons:
- DALL-E, Midjourney, Stable Diffusion
- Prompt: "Modern minimalist app icon for AI email assistant, purple gradient, envelope with sparkle, flat design, white background"

## Required Sizes
- **16x16**: Toolbar icon (Chrome/Edge)
- **48x48**: Extension management page
- **128x128**: Chrome Web Store listing

## Design Guidelines
- Keep it simple and recognizable at small sizes
- Use high contrast (icon should be visible on light and dark backgrounds)
- Avoid text or fine details (won't be readable at 16x16)
- Match brand colors (purple gradient: #667eea to #764ba2)
- Follow platform guidelines:
  - Chrome: https://developer.chrome.com/docs/webstore/images/
  - Firefox: https://extensionworkshop.com/documentation/develop/add-on-icons/

## Current Placeholder
The SVG template shows:
- Purple gradient background circle
- White envelope (email symbol)
- Gold sparkle (AI symbol)
- Clean, modern design

Replace `icon-16.png`, `icon-48.png`, and `icon-128.png` with your final designs before publishing.
