from PIL import Image, ImageDraw
import hashlib, random

def get_safe_tiles(seed):
    hashed = hashlib.sha256(seed.encode()).hexdigest()
    random.seed(hashed)
    return random.sample(range(25), 5)

def generate_prediction_image(seed):
    grid_size = 5
    tile_size = 100
    spacing = 10
    width = height = grid_size * (tile_size + spacing) - spacing
    image = Image.new("RGB", (width, height), "#111")
    draw = ImageDraw.Draw(image)

    safe_tiles = get_safe_tiles(seed)
    for i in range(25):
        row, col = divmod(i, grid_size)
        x = col * (tile_size + spacing)
        y = row * (tile_size + spacing)
        if i in safe_tiles:
            draw.rectangle([x, y, x+tile_size, y+tile_size], fill="#00ff77")
            draw.text((x + 35, y + 35), "💎", fill="black")
        else:
            draw.rectangle([x, y, x+tile_size, y+tile_size], fill="#333")

    return image
