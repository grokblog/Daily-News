import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_image(filename, text, size=(800, 600), color=(52, 152, 219), text_color=(255, 255, 255)):
    img = Image.new('RGB', size, color=color)
    d = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", size=int(min(size)/2))
    except (IOError, OSError):
        font = ImageFont.load_default()
        
    # Get text size
    # In newer Pillow versions, textsize is deprecated, use textbbox
    if hasattr(d, 'textbbox'):
        left, top, right, bottom = d.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
    else:
        text_width, text_height = d.textsize(text, font=font)
        
    position = ((size[0]-text_width)/2, (size[1]-text_height)/2)
    
    d.text(position, text, fill=text_color, font=font)
    
    # Save
    img.save(filename)
    print(f"Created {filename}")

def main():
    # Directories
    template_assets_dir = Path("templates/assets/images")
    public_assets_dir = Path("public/assets/images")
    public_images_dir = Path("public/images")
    
    template_assets_dir.mkdir(parents=True, exist_ok=True)
    public_assets_dir.mkdir(parents=True, exist_ok=True)
    public_images_dir.mkdir(parents=True, exist_ok=True)
    
    # Author Avatar (Square)
    create_placeholder_image(
        template_assets_dir / "author-avatar.jpg", 
        "A", 
        size=(200, 200), 
        color="#34495e"
    )
    
    # Favicon (Small Square)
    create_placeholder_image(
        template_assets_dir / "favicon.png", 
        "V", 
        size=(64, 64), 
        color="#e74c3c"
    )
    # Copy to public root for favicon too (optional)
    create_placeholder_image(
        Path("public/assets/favicon.png"), 
        "V", 
        size=(64, 64), 
        color="#e74c3c"
    )

    # Logo (Rectangle) - Optional if SVG fails
    create_placeholder_image(
        template_assets_dir / "logo.png",
        "ViralNews",
        size=(300, 80),
        color="#ffffff",
        text_color="#2c3e50"
    )

    # Featured Placeholder
    create_placeholder_image(
        public_images_dir / "featured-placeholder.jpg",
        "Featured Image",
        size=(1200, 630),
        color="#95a5a6",
        text_color="#ffffff"
    )

    print("Assets created successfully.")

if __name__ == "__main__":
    main()
