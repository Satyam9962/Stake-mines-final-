from PIL import Image
import random
import os

GRID_SIZE = 5
TILE_SIZE = 100

BASE_IMAGE_PATH = "assets/base_grid.png"
SAFE_TILE_CROP = (100, 0, 200, 100)   # Green diamond part from your image
CLOSED_TILE_CROP = (0, 0, 100, 100)   # Closed box part

def load_tiles():
    base = Image.open(BASE_IMAGE_PATH).convert("RGBA")
    safe_tile = base.crop(SAFE_TILE_CROP)
    closed_tile = base.crop(CLOSED_TILE_CROP)
    return safe_tile, closed_tile

def get_safe_tiles(seed: str):
    random.seed(seed)
    positions = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)]
    return random.sample(positions, 5)

def generate_prediction_image(seed: str):
    safe_tile_img, closed_tile_img = load_tiles()
    safe_tiles = get_safe_tiles(seed)

    img = Image.new("RGBA", (GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE), (24, 26, 33, 255))

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            if (row, col) in safe_tiles:
                img.paste(safe_tile_img.resize((TILE_SIZE, TILE_SIZE)), (x, y))
            else:
                img.paste(closed_tile_img.resize((TILE_SIZE, TILE_SIZE)), (x, y))

    os.makedirs("predictions", exist_ok=True)
    output_path = f"predictions/{seed}.png"
    img.save(output_path)
    return output_path
