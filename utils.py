import json
import os
import random
from PIL import Image

def load_user_data():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

def save_user_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

def generate_safe_tiles(seed):
    random.seed(seed)
    return random.sample(range(25), 5)

def generate_prediction_image(seed, safe_tiles):
    box_size = 100
    grid_size = 5
    image = Image.new("RGBA", (box_size * grid_size, box_size * grid_size), (255, 255, 255, 0))

    safe_img = Image.open("safe_box.png").resize((box_size, box_size))
    closed_img = Image.open("closed_box.png").resize((box_size, box_size))

    for i in range(grid_size):
        for j in range(grid_size):
            index = i * grid_size + j
            if index in safe_tiles:
                image.paste(safe_img, (j * box_size, i * box_size), safe_img)
            else:
                image.paste(closed_img, (j * box_size, i * box_size), closed_img)

    return image
