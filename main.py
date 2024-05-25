import os
import json
import ntpath
from typing import Type, Any

from PIL import Image, ImageCms
from pydantic import BaseModel

OUTPUT_DIR = "output"
INPUT_DIR = "input"

Image.MAX_IMAGE_PIXELS = None


class Template(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    image: Image.Image
    info: dict

    ratio: str = None
    box_width: int = None
    box_height: int = None

    rotated: bool = False

    def __init__(self, **data: Any):
        super().__init__(**data)
        for key, value in self.info.items():
            dimensions = value.split("x")
            self.box_width = int(dimensions[0])
            self.box_height = int(dimensions[1])
            self.ratio = key

        if self.image.width > self.image.height:
            self.image = self.image.rotate(90, expand=True)
            self.rotated = True

    def resize_fit(self) -> Image.Image:
        resized_image = self.image.resize((self.box_width, self.box_height))

        if self.rotated:
            return resized_image.rotate(270, expand=True)

        return resized_image

    def resize_fill(self) -> Image.Image:
        aspect_ratio = self.image.width / self.image.height

        new_width = max(self.box_width, int(self.box_height * aspect_ratio))
        new_height = max(self.box_height, int(self.box_width / aspect_ratio))

        resized_image = self.image.resize((new_width, new_height))

        filled_image = Image.new("RGB", (self.box_width, self.box_height))

        x_offset = (self.box_width - new_width) // 2
        y_offset = (self.box_height - new_height) // 2

        filled_image.paste(resized_image, (x_offset, y_offset))

        if self.rotated:
            return filled_image.rotate(270, expand=True)

        return filled_image

    def rotate_image(self):
        self.image.rotate(180, expand=True)


def load_json_db(file_path: str):
    with open(file_path) as file:
        return json.load(file)


def get_file_name(path: str, extension: bool = True) -> str:
    if not extension:
        return str(ntpath.basename(path)).split(".")[0]
    return ntpath.basename(path)


def images_to_list(directory_path: str) -> list:
    images_list = os.listdir(directory_path)
    images_list = [
        image
        for image in images_list
        if image.endswith(".png") or image.endswith(".jpg") or image.endswith(".jpeg")
    ]

    return images_list


if __name__ == "__main__":
    db = load_json_db("db.json")

    images_list = images_to_list(INPUT_DIR)

    profile = ImageCms.ImageCmsProfile("profiles\\USWebCoatedSWOP.icc")

    for img in images_list:
        process_image = Image.open(f"{INPUT_DIR}\\{img}")

        if not os.path.exists(f"{OUTPUT_DIR}\\{get_file_name(img, False)}"):
            os.makedirs(f"{OUTPUT_DIR}\\{get_file_name(img, False)}")

        print(get_file_name(img))

        for size in db:
            tmp = Template(image=process_image, info=size)

            print(tmp)

            fit_image = tmp.resize_fit()
            fit_image.convert("RGB").save(
                f"{OUTPUT_DIR}\\{get_file_name(img, False)}\\{tmp.ratio}_fit_{get_file_name(img, False)}.jpeg",
                icc_profile=profile.tobytes(),
                dpi=(300, 300),
            )

            # if not tmp.ratio == "3x4":
            fill_image = tmp.resize_fill()
            fill_image.convert("RGB").save(
                f"{OUTPUT_DIR}\\{get_file_name(img, False)}\\{tmp.ratio}_fill_{get_file_name(img, False)}.jpeg",
                icc_profile=profile.tobytes(),
                dpi=(300, 300),
            )

        print(f"-------------------------------\n")
