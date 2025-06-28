from PIL import Image, ImageDraw
import hashlib
import random

def generate_prediction_image(seed: str) -> Image.Image:
    hash_val = hashlib.sha256(seed.encode()).hexdigest()
    random.seed(hash_val)
    safe_tiles = random.sample(range(25), 5)
    tile_size = 100
    grid_size = 5
    img = Image.new("RGBA", (tile_size * grid_size, tile_size * grid_size), (30, 35, 45))

    tile = Image.open("green_diamond_tile.png").resize((tile_size, tile_size))

    for i in range(25):
        x = (i % grid_size) * tile_size
        y = (i // grid_size) * tile_size
        if i in safe_tiles:
            img.paste(tile, (x, y), mask=tile if tile.mode == 'RGBA' else None)
        else:
            ImageDraw.Draw(img).rectangle([x, y, x + tile_size, y + tile_size], fill=(50, 55, 65))

    return img
