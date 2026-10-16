"""Pixel avatar generator for Habit Streak Bot"""
from PIL import Image, ImageDraw, ImageFont
import io
import base64

def generate_avatar(stage: int, size: int = 256) -> bytes:
    """Generate a pixel-art style avatar based on stage (1-6)"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Color palettes per stage
    palettes = {
        1: {"skin": (255, 220, 177), "hair": (101, 67, 33), "eyes": (50, 50, 50), 
            "shirt": (100, 149, 237), "bg": (240, 240, 240)},
        2: {"skin": (255, 220, 177), "hair": (101, 67, 33), "eyes": (50, 50, 50),
            "shirt": (100, 149, 237), "pants": (50, 50, 50), "bg": (200, 230, 255),
            "belt": (139, 90, 43)},
        3: {"skin": (255, 220, 177), "hair": (101, 67, 33), "eyes": (50, 50, 50),
            "shirt": (100, 149, 237), "pants": (50, 50, 50), "bg": (255, 200, 150),
            "belt": (139, 90, 43), "sword": (192, 192, 192)},
        4: {"skin": (255, 220, 177), "hair": (101, 67, 33), "eyes": (50, 50, 50),
            "shirt": (100, 149, 237), "pants": (50, 50, 50), "bg": (255, 180, 100),
            "belt": (139, 90, 43), "sword": (192, 192, 192), "cape": (178, 34, 34)},
        5: {"skin": (255, 220, 177), "hair": (101, 67, 33), "eyes": (50, 50, 50),
            "shirt": (100, 149, 237), "pants": (50, 50, 50), "bg": (255, 160, 50),
            "belt": (139, 90, 43), "sword": (255, 215, 0), "cape": (178, 34, 34),
            "crown": (255, 215, 0), "aura": (255, 255, 200, 100)},
        6: {"skin": (255, 220, 177), "hair": (101, 67, 33), "eyes": (50, 50, 50),
            "shirt": (100, 149, 237), "pants": (50, 50, 50), "bg": (255, 140, 0),
            "belt": (139, 90, 43), "sword": (255, 215, 0), "cape": (178, 34, 34),
            "crown": (255, 215, 0), "aura": (255, 255, 200, 150), 
            "wings": (255, 255, 255, 200)},
    }

    p = palettes.get(min(stage, 6), palettes[1])

    # Background
    draw.rectangle([0, 0, size, size], fill=p["bg"])

    # Pixel size for retro look
    ps = size // 32

    # Helper to draw pixel blocks
    def pixel_rect(x, y, w, h, color):
        draw.rectangle([x*ps, y*ps, (x+w)*ps, (y+h)*ps], fill=color)

    # Aura (stage 5+)
    if stage >= 5 and "aura" in p:
        for i in range(8):
            offset = i * 2
            alpha = 30 - i * 3
            aura_color = (*p["aura"][:3], alpha)
            draw.ellipse([offset*ps, offset*ps, (32-offset)*ps, (32-offset)*ps], 
                        fill=aura_color)

    # Wings (stage 6)
    if stage >= 6 and "wings" in p:
        # Left wing
        pixel_rect(2, 10, 6, 12, p["wings"])
        pixel_rect(1, 12, 2, 8, p["wings"])
        # Right wing
        pixel_rect(24, 10, 6, 12, p["wings"])
        pixel_rect(29, 12, 2, 8, p["wings"])

    # Cape (stage 4+)
    if stage >= 4 and "cape" in p:
        pixel_rect(8, 12, 16, 18, p["cape"])

    # Body
    pixel_rect(12, 14, 8, 10, p["shirt"])
    pixel_rect(12, 24, 8, 6, p.get("pants", (50, 50, 50)))

    # Belt
    if "belt" in p:
        pixel_rect(12, 22, 8, 2, p["belt"])

    # Head
    pixel_rect(11, 6, 10, 10, p["skin"])

    # Hair
    pixel_rect(11, 4, 10, 4, p["hair"])
    pixel_rect(10, 6, 2, 6, p["hair"])
    pixel_rect(20, 6, 2, 6, p["hair"])

    # Eyes
    pixel_rect(13, 9, 2, 2, p["eyes"])
    pixel_rect(17, 9, 2, 2, p["eyes"])

    # Sword (stage 3+)
    if stage >= 3 and "sword" in p:
        pixel_rect(22, 16, 2, 10, p["sword"])
        pixel_rect(21, 14, 4, 2, p.get("belt", (139, 90, 43)))

    # Crown (stage 5+)
    if stage >= 5 and "crown" in p:
        pixel_rect(10, 3, 12, 3, p["crown"])
        pixel_rect(12, 1, 2, 3, p["crown"])
        pixel_rect(18, 1, 2, 3, p["crown"])

    # Stage indicator text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size//8)
    except:
        font = ImageFont.load_default()

    text = f"Lv.{stage}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_x = (size - text_w) // 2
    draw.text((text_x, size - size//6), text, fill=(50, 50, 50), font=font)

    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def generate_heatmap(user_checkins, habits, days=30, size=(800, 400)) -> bytes:
    """Generate a heatmap of check-ins over time"""
    from datetime import datetime, timedelta
    import math

    img = Image.new('RGB', size, (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Color intensity based on completion rate
    colors = {
        0: (235, 235, 235),      # No data
        1: (198, 228, 139),      # Light green
        2: (123, 201, 111),      # Medium green
        3: (35, 154, 59),        # Dark green
        4: (25, 97, 39),         # Very dark green
    }

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)

    # Grid settings
    cols = 7  # Days per week
    rows = math.ceil(days / cols)
    cell_w = (size[0] - 100) // cols
    cell_h = (size[1] - 80) // rows
    cell_size = min(cell_w, cell_h) - 4

    # Day labels
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, name in enumerate(day_names):
        x = 60 + i * (cell_size + 6)
        draw.text((x, 10), name, fill=(100, 100, 100))

    # Build check-in lookup
    checkin_dates = {}
    for checkin in user_checkins:
        d = checkin.checked_at.date()
        checkin_dates[d] = checkin_dates.get(d, 0) + 1

    # Draw cells
    for day_offset in range(days):
        date = start_date + timedelta(days=day_offset)
        count = checkin_dates.get(date, 0)

        intensity = min(count, 4)
        color = colors[intensity]

        week = day_offset // 7
        day_of_week = date.weekday()

        x = 60 + day_of_week * (cell_size + 6)
        y = 40 + week * (cell_size + 6)

        draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color, outline=(200, 200, 200))

        # Date number
        if cell_size > 20:
            draw.text((x + 2, y + 2), str(date.day), fill=(80, 80, 80))

    # Legend
    legend_y = size[1] - 30
    draw.text((10, legend_y), "Less", fill=(100, 100, 100))
    for i, color in colors.items():
        draw.rectangle([60 + i*25, legend_y, 80 + i*25, legend_y + 15], fill=color)
    draw.text((60 + len(colors)*25 + 5, legend_y), "More", fill=(100, 100, 100))

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def generate_streak_badge(streak_count: int, size: int = 512) -> bytes:
    """Generate a streak celebration badge"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background gradient simulation
    for i in range(size):
        r = int(255 - i * 0.1)
        g = int(200 - i * 0.2)
        b = int(100 + i * 0.3)
        draw.line([(0, i), (size, i)], fill=(r, g, b, 255))

    # Flame circle
    center = size // 2
    radius = size // 3

    # Outer glow
    for r in range(radius + 40, radius, -2):
        alpha = int((radius + 40 - r) * 6)
        draw.ellipse([center - r, center - r, center + r, center + r], 
                    fill=(255, 100, 0, min(alpha, 255)))

    # Main circle
    draw.ellipse([center - radius, center - radius, center + radius, center + radius], 
                fill=(255, 140, 0))

    # Inner highlight
    draw.ellipse([center - radius//2, center - radius//2, center + radius//2, center + radius//2], 
                fill=(255, 200, 50))

    # Streak number
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size//4)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size//10)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text = str(streak_count)
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((center - text_w//2, center - text_h//2 - 10), text, 
              fill=(255, 255, 255), font=font_large, stroke_width=3, stroke_fill=(200, 50, 0))

    label = "DAY STREAK"
    bbox = draw.textbbox((0, 0), label, font=font_small)
    text_w = bbox[2] - bbox[0]
    draw.text((center - text_w//2, center + size//8), label, 
              fill=(255, 255, 255), font=font_small, stroke_width=2, stroke_fill=(150, 50, 0))

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()
