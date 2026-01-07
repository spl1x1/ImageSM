import json
from operator import contains
from typing import Any

import numpy as np
import PIL.Image as Image
import argparse


class ImageManager:
    def __init__(self, filename: str):
        self.image = Image.open(filename)
        self.pixels = np.array(self.image)
        self.rectangles = []
        self.splicedImages = []

    def add_rectangle(self, x_start: int, y_start: int, x_end: int, y_end: int):
        rect_pixels = self.pixels[y_start:y_end, x_start:x_end]
        self.rectangles.append({
            'pixels': rect_pixels,
            'width': x_end - x_start,
            'height': y_end - y_start
        })

    def save_spliced_image(self, filename: str, layout='horizontal'):
        if not self.rectangles:
            return

        channels = self.pixels.shape[2] if self.pixels.ndim == 3 else 1

        if layout == 'horizontal':
            total_width = sum(r['width'] for r in self.rectangles)
            max_height = max(r['height'] for r in self.rectangles)
            final_pixels = np.zeros((max_height, total_width, channels), dtype=np.uint8)

            x_offset = 0
            for rect in self.rectangles:
                w, h = rect['width'], rect['height']
                final_pixels[:h, x_offset:x_offset + w] = rect['pixels']
                x_offset += w
        else:  # vertical
            max_width = max(r['width'] for r in self.rectangles)
            total_height = sum(r['height'] for r in self.rectangles)
            final_pixels = np.zeros((total_height, max_width, channels), dtype=np.uint8)

            y_offset = 0
            for rect in self.rectangles:
                w, h = rect['width'], rect['height']
                final_pixels[y_offset:y_offset + h, :w] = rect['pixels']
                y_offset += h

        new_image = Image.fromarray(final_pixels, mode='RGBA' if channels == 4 else 'RGB')
        new_image.save(filename)
        self.splicedImages.append(filename)


class JSONManager:
    def __init__(self, width: int, height: int, texture_name: str):
        self.width = width
        self.height = height
        self.JSONData = {"TextureName: ": texture_name, "Width": width, "Height": height}

    def insert(self, key: str, value: Any):
        self.JSONData[key] = value

    def save_to_file(self, filename: str):
        with open(filename, 'w') as file:
            json.dump(self.JSONData, file, indent=4)

    def __str__(self):
        return json.dumps(self.JSONData, indent=4)


def input_texture_details() -> list[int]:
    texture_details = [-1, -1]
    try:
        texture_details[0] = int(input("Enter width: ").strip())
        texture_details[1] = int(input("Enter height: ").strip())
    except ValueError:
        print("Invalid input for width or height. Please enter integers.")
    return texture_details

def main(args):
    texture = str()
    details= [-1, -1]

    while texture == "":
        texture =input("Enter texture name: ").strip()
    while -1 in details:
        details = input_texture_details()

    texture_json = JSONManager(details[0], details[1], texture)
    print(texture_json)
    texture_json.save_to_file(args.output if args.output else args.texture + ".json")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ImageSM',
        description='Prepares images and creates json for parsing to game engine',
        epilog='Example: ImageSM input.png output.png')

    parser.add_argument('filename', help='Input file name')
    parser.add_argument('output', help='Output file name', default=None, nargs='?')

    arguments = parser.parse_args()
    main(arguments)

