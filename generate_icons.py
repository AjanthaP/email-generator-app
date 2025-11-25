"""Generate placeholder PNG icons for the browser extension."""
from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
icons_dir = "browser-extension/icons"
os.makedirs(icons_dir, exist_ok=True)

# Define sizes
sizes = [16, 48, 128]

for size in sizes:
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient circle (simplified to solid purple)
    circle_color = (102, 126, 234, 255)  # Purple from gradient
    draw.ellipse([0, 0, size-1, size-1], fill=circle_color)
    
    # Draw white envelope emoji or text
    try:
        # Try to use a font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw simple white circle in center as placeholder
    center = size // 2
    radius = size // 4
    draw.ellipse([center - radius, center - radius, 
                  center + radius, center + radius], 
                 fill=(255, 255, 255, 255))
    
    # Save the icon
    icon_path = f"{icons_dir}/icon{size}.png"
    img.save(icon_path, 'PNG')
    print(f"✓ Created {icon_path}")

print("\n✅ All icons generated successfully!")
print("📁 Icons saved in: browser-extension/icons/")
print("\nYou can now load the extension in Chrome.")
