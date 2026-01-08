import json

import numpy as np
import PIL.Image as Image
import argparse
from enum import Enum


class ImageManager:
    def __init__(self, filename: str):
        self.image = Image.open(filename)
        self.pixels = np.array(self.image)
        self.rectangles = []
        self.splicedImages = []

    def change_file(self, filename: str):
        self.image = Image.open(filename)
        self.pixels = np.array(self.image)
        self.rectangles = []

    def clear_rectangles(self):
        self.rectangles = []

    def add_rectangle(self, x_start: int, y_start: int, x_end: int, y_end: int):
        rect_pixels = self.pixels[y_start:y_end, x_start:x_end]
        self.rectangles.append({
            'pixels': rect_pixels,
            'width': x_end - x_start,
            'height': y_end - y_start
        })

    def splice_image(self):
        if not self.rectangles:
            return

        channels = self.pixels.shape[2] if self.pixels.ndim == 3 else 1
        total_width = sum(r['width'] for r in self.rectangles)
        max_height = max(r['height'] for r in self.rectangles)
        final_pixels = np.zeros((max_height, total_width, channels), dtype=np.uint8)

        x_offset = 0
        for rect in self.rectangles:
            w, h = rect['width'], rect['height']
            final_pixels[:h, x_offset:x_offset + w] = rect['pixels']
            x_offset += w

        new_image = Image.fromarray(final_pixels, mode='RGBA' if channels == 4 else 'RGB')
        self.splicedImages.append(new_image)

    def stitch_images(self, output_filename: str):
        widths, heights = zip(*(img.size for img in self.splicedImages))

        max_width = max(widths)
        total_height = sum(heights)

        new_image = Image.new('RGBA', (max_width, total_height))

        y_offset = 0
        for img in self.splicedImages:
            new_image.paste(img, (0, y_offset))
            y_offset += img.size[1]

        new_image.save(output_filename)
        self.splicedImages.append(output_filename)


class JSONManager:
    def __init__(self, texture_name: str ,width: int, height: int):
        self.JSONData = None
        self.width = width
        self.height = height
        self.JSONData= {"spriteInfo": {"TextureName: ": texture_name, "Width": width, "Height": height}}

    def insert(self, key: str, x: int, y: int):
        self.JSONData[key] = {"x": x, "y": y, "w": self.width, "h": self.height}
    def save_to_file(self, filename: str):
        with open(filename, 'w') as file:
            json.dump(self.JSONData, file, indent=4)

    def __str__(self):
        return json.dumps(self.JSONData, indent=4)

def get_int(prompt: str) -> int:
    value = -1
    while value < 0:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter a positive integer.")
    return value

class Animations(Enum):
    NONE = '',
    IDLE = 'IDLE',
    RUNNING = 'RUNNING',
    ATTACK = 'ATTACK',
    INTERACT = 'INTERACT',
    DYING = 'DYING'

class Directions(Enum):
    OMNI = '',
    UP = 'UP',
    DOWN = 'DOWN',
    LEFT ='LEFT',
    RIGHT = 'RIGHT'


def iterate_over_enum(enum_class):
    pos = 0
    for index, (name, value) in enumerate(enum_class.__members__.items()):
        pos += 1
        print(f"{pos}. {name}")

def enum_to_string(enum_class, index):
    members = list(enum_class.__members__.keys())
    if 0 <= index < len(members):
        return members[index]
    return None

def get_animation_type():
    print("Animation type options:")
    iterate_over_enum(Animations)
    anim_index = get_int("Select animation: ") - 1
    item = enum_to_string(Animations, anim_index)
    if item is not None:
        return item
    else:
        print("Invalid animation type.")
    return ""

def get_direction_type():
    print("Direction options:")
    iterate_over_enum(Directions)
    dir_index = get_int("Select direction: ") - 1
    item = enum_to_string(Directions, dir_index)
    if item is not None:
        return item
    else:
        print("Invalid direction type.")
    return ""

def main(args):
    width = get_int("Enter width: ")
    height = get_int("Enter height: ")
    texture_name = input("Enter texture name: ").strip()
    texture_json = JSONManager(texture_name,width, height)
    image_manager = ImageManager(args.files[0])

    while True:
        frame_count = get_int("Enter number of frames: ")

        animation_type = get_animation_type()
        direction_type = get_direction_type()

        context = f"{texture_name}_{animation_type}${direction_type}"

        same_x = input("Are all frames at the same x coordinate? (y/n): ").strip().lower() == 'y'
        same_y = input("Are all frames at the same y coordinate? (y/n): ").strip().lower() == 'y'
        iteration_based_x = False
        iteration_based_y = False
        if not same_x:
            iteration_based_x = input("Is the x coordinate based on frame iteration? (y/n): ").strip().lower() == 'y'
        if not same_y:
            iteration_based_y = input("Is the y coordinate based on frame iteration? (y/n): ").strip().lower() == 'y'
        if not same_y:
            print("You will be prompted to enter y coordinate for each frame.")

        x = get_int("Enter x coordinate: ")
        y = get_int("Enter y coordinate: ")
        for i in range(frame_count):
            if not same_x and not iteration_based_x:
                x = get_int("Enter x coordinate: ")
            if not same_y and not iteration_based_y:
                y = get_int("Enter y coordinate: ")

            current_x = x
            current_y = y
            if iteration_based_x:
                current_x = x + i * width
            if iteration_based_y:
                current_y = y + i * height

            texture_json.insert(context if i==0 else (context + f"_{i+1}"), current_x, current_y)
            image_manager.add_rectangle(current_x, current_y, current_x+width, current_y+height)

        image_manager.splice_image()
        image_manager.clear_rectangles()

        if input("Do you want to add another animation? (y/n): ").strip().lower()== 'n':
            break

        if len(args.files) == 1:
            continue
        change_file = input("Do you want to change the input file? (y/n): ").strip().lower()

        if change_file == 'y':
            print("File options:")
            for idx, f in enumerate(args.files):
                print(f"{idx + 1}. {f}")
            file_index = get_int("Select the file number: ") - 1
            if 0 <= file_index < len(args.files):
                image_manager.change_file(args.files[file_index])
            else:
                print("Invalid file number. Continuing with the current file.")

    texture_json.save_to_file(texture_name + ".json")
    image_manager.stitch_images(texture_name + ".png")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ImageSM',
        description='Prepares images and creates json for parsing to game engine',
        epilog='Example: ImageSM input.png output.png')

    parser.add_argument('files', nargs='+', help='Input files')

    arguments = parser.parse_args()
    main(arguments)

