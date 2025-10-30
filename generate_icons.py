#!/usr/bin/env python3
"""
PWA Icons Generator
Creates all required PWA icons from a single SVG source
"""

import os
from PIL import Image, ImageDraw
import math

def create_icon(size):
    """Create a PWA icon with specified size"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define colors
    primary_color = (31, 41, 55)  # #1f2937
    secondary_color = (59, 130, 246)  # #3b82f6
    accent_color = (16, 185, 129)  # #10b981
    
    # Calculate dimensions based on size
    padding = size // 10
    inner_size = size - (2 * padding)
    
    # Draw background circle
    circle_bbox = [padding, padding, padding + inner_size, padding + inner_size]
    draw.ellipse(circle_bbox, fill=primary_color)
    
    # Draw inner circle (slightly lighter)
    inner_padding = inner_size // 8
    inner_circle_bbox = [
        padding + inner_padding, 
        padding + inner_padding,
        padding + inner_size - inner_padding,
        padding + inner_size - inner_padding
    ]
    draw.ellipse(inner_circle_bbox, fill=secondary_color)
    
    # Draw GitHub icon (simplified)
    github_size = inner_size // 3
    github_x = (size - github_size) // 2
    github_y = (size - github_size) // 2
    
    # Draw GitHub outline (octagon-like shape)
    github_points = []
    center_x, center_y = github_x + github_size // 2, github_y + github_size // 2
    radius = github_size // 3
    
    for i in range(8):
        angle = i * math.pi / 4
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        github_points.append((int(x), int(y)))
    
    draw.polygon(github_points, fill='white')
    
    # Draw AI symbol (small dots in center)
    dot_radius = size // 50
    center_offset = github_size // 6
    
    # Small dots representing AI
    dot_positions = [
        (center_x - center_offset, center_y),
        (center_x, center_y - center_offset),
        (center_x + center_offset, center_y),
        (center_x, center_y + center_offset)
    ]
    
    for dot_x, dot_y in dot_positions:
        draw.ellipse([
            dot_x - dot_radius, dot_y - dot_radius,
            dot_x + dot_radius, dot_y + dot_radius
        ], fill=accent_color)
    
    return img

def generate_all_icons():
    """Generate all required PWA icon sizes"""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    icons_dir = "/workspace/frontend/public/icons"
    
    # Ensure icons directory exists
    os.makedirs(icons_dir, exist_ok=True)
    
    print("🎨 Generating PWA icons...")
    
    for size in sizes:
        # Create icon
        icon = create_icon(size)
        
        # Save icon
        icon_path = os.path.join(icons_dir, f"icon-{size}x{size}.png")
        icon.save(icon_path, "PNG")
        print(f"✅ Created {icon_path}")
    
    # Create shortcut icons
    shortcut_sizes = [96]
    for size in shortcut_sizes:
        # Dashboard shortcut
        dashboard_icon = create_icon(size)
        dashboard_path = os.path.join(icons_dir, "shortcut-dashboard.png")
        dashboard_icon.save(dashboard_path, "PNG")
        
        # Settings shortcut
        settings_icon = create_icon(size)
        settings_path = os.path.join(icons_dir, "shortcut-settings.png")
        settings_icon.save(settings_path, "PNG")
        
        print(f"✅ Created shortcut icons")
    
    print("🎉 All PWA icons generated successfully!")

if __name__ == "__main__":
    generate_all_icons()