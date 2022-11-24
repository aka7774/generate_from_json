import math
import os
import sys
import traceback
import random
import json
import platform
import subprocess as sp
import copy
import re
import pprint
import itertools
import time

from PIL import Image, ImageDraw, ImageFont
from glob import glob
import gradio as gr

import modules.scripts as scripts
from modules import sd_samplers, sd_models, shared
from modules.processing import Processed, process_images
from modules.shared import opts, cmd_opts, state
from modules.hypernetworks import hypernetwork

from extensions.generate_from_json.py import const

def upscale(image, scaler_index, resize, mode, resize_w, resize_h, crop):
    upscaler = shared.sd_upscalers[scaler_index]
    c = upscaler.scaler.upscale(image, resize, upscaler.data_path)
    if mode == 1 and crop:
        cropped = Image.new("RGB", (resize_w, resize_h))
        cropped.paste(c, box=(resize_w // 2 - c.width // 2, resize_h // 2 - c.height // 2))
        c = cropped
    return c

def extra_outputs(fn, images):
    with open(const.CONFIG_FILE) as f:
        data = json.load(f)

        if ("webp_quality" in data):
            webp_quality = int(data["webp_quality"])

        if ("upscaler" in data):
            i = 0
            for upscaler in shared.sd_upscalers:
                if upscaler.name == data["upscaler"]:
                    extras_upscaler_1 = i
                    break
                i += 1
                
        if ("upscaling_resize" in data):
            upscaling_resize = float(data["upscaling_resize"])
        if ("upscaling_resize_w" in data):
            upscaling_resize_w = int(data["upscaling_resize_w"])
        if ("upscaling_resize_h" in data):
            upscaling_resize_h = int(data["upscaling_resize_h"])
        if ("upscaling_crop" in data):
            upscaling_crop = int(data["upscaling_crop"])

        if ("imagefont_truetype" in data):
            imagefont_truetype = data["imagefont_truetype"]
        if ("imagefont_truetype_index" in data):
            imagefont_truetype_index = int(data["imagefont_truetype_index"])
        if ("imagefont_truetype_size" in data):
            imagefont_truetype_size = int(data["imagefont_truetype_size"])

        if ("draw_text_left" in data):
            draw_text_left = int(data["draw_text_left"])
        if ("draw_text_top" in data):
            draw_text_top = int(data["draw_text_top"])
        if ("draw_text_color" in data):
            draw_text_color = data["draw_text_color"]
        if ("draw_text" in data):
            draw_text = data["draw_text"]
        del data

    if webp_quality == None:
        return images

    for image in images:
        image = image.convert("RGB")

        if extras_upscaler_1 > 0:
            if upscaling_resize == 1.0:
                resize_mode = 1
                upscaling_resize = max(upscaling_resize_w/image.width, upscaling_resize_h/image.height)
            else:
                resize_mode = 0
                upscaling_resize_w = image.width * upscaling_resize
                upscaling_resize_h = image.height * upscaling_resize

            res = upscale(image, extras_upscaler_1, upscaling_resize, resize_mode, upscaling_resize_w, upscaling_resize_h, upscaling_crop)
            image = res

        # webp text
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(imagefont_truetype, index=imagefont_truetype_index, size=imagefont_truetype_size)
        draw.text((draw_text_left, draw_text_top), draw_text, draw_text_color, font=font)

        # webp save
        webp_dst = os.path.join(const.WEBP_DIR, f"{fn}.webp")
        if os.path.exists(webp_dst):
            image.save(os.path.join(const.WEBP_DIR, f"{fn}-{float(time.time())}.webp"), quality=webp_quality)
        else:
            image.save(webp_dst, quality=webp_quality)
