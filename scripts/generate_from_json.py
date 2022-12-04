import os
import sys
import platform
import subprocess as sp

import gradio as gr

import modules.scripts as scripts
from modules.processing import Processed, process_images
from modules.shared import opts, cmd_opts, state

from py import const
from py.generate_json_images import generate_json_images

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

class Script(scripts.Script):
    def title(self):
        return "Generate from json"

    def ui(self, is_img2img):
        open_json_directory = gr.Button("Open JSON Directory")
        open_json_directory.click(fn=open_json_directory_click)
        open_webp_directory = gr.Button("Open WEBP Directory")
        open_webp_directory.click(fn=open_webp_directory_click)

        return []

    def on_show(self):
        return [gr.Textbox.update(visible=True),
                gr.Button.update(visible=True),
                ]

    def run(self, p):
        p.do_not_save_grid = True
        return Processed(p, generate_json_images(p), p.seed, "")
