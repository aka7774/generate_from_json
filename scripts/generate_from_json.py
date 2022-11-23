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
from extensions.generate_from_json.py.generate_json_images import generate_json_images

const.JSON_DIR = os.path.join('extensions', 'generate_from_json', 'json')
const.WEBP_DIR = os.path.join('extensions', 'generate_from_json', 'webp')
const.CONFIG_FILE = os.path.join('extensions', 'generate_from_json', 'config.json')

def open_folder(f):
    if not os.path.isdir(f):
        print(f"""
WARNING
An open_folder request was made with an argument that is not a folder.
This could be an error or a malicious attempt to run code on your computer.
Requested path was: {f}
""", file=sys.stderr)
        return

    if not cmd_opts.hide_ui_dir_config:
        path = os.path.normpath(f)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            sp.Popen(["open", path])
        else:
            sp.Popen(["xdg-open", path])

def open_json_directory_click():
    return open_folder(const.JSON_DIR)

def open_webp_directory_click():
    return open_folder(const.WEBP_DIR)

def text_button_onclick():
    pprint.pprint('clicked')
    return []

class Script(scripts.Script):
    def title(self):
        return "Generate from json"

    def ui(self, is_img2img):
        open_json_directory = gr.Button("Open JSON Directory")
        open_json_directory.click(fn=open_json_directory_click)
        open_webp_directory = gr.Button("Open WEBP Directory")
        open_webp_directory.click(fn=open_webp_directory_click)

        #text_button = gr.Button("Test")
        #text_button.click(text_button_onclick, inputs=[], outputs=[])
        return []

    def on_show(self):
        return [gr.Textbox.update(visible=True),
                gr.Button.update(visible=True),
                ]

    def run(self, p):
        p.do_not_save_grid = True
        return Processed(p, generate_json_images(p), p.seed, "")
