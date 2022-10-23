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

import modules.scripts as scripts
import gradio as gr

from modules.processing import Processed, process_images
from PIL import Image
from modules.shared import opts, cmd_opts, state
from modules import sd_samplers
from glob import glob


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


class Script(scripts.Script):
    def title(self):
        return "Generate from json"

    def ui(self, is_img2img):
        with gr.Row():
            directory = gr.Textbox(label="Prompts Directory",
                                   value="prompts", interactive=True)
            open_directory = gr.Button("Open Prompts Directory")
            open_directory.click(
                fn=open_folder,
                inputs=directory,
                outputs=[],
            )

        return [directory, open_directory]

    def on_show(self, directory, open_directory):
        return [gr.Textbox.update(visible=True),
                gr.Button.update(visible=True),
                ]

    def run(self, p, directory, open_directory):
        p.do_not_save_grid = True

        files = glob(directory + "/*.json")

        jobs = []
        for fn in files:
            with open(fn) as f:
                data = json.load(f)
                job = dict()

                for k, v in data.items():
                    if re.match(r"^(width|height|cfg_scale|steps|sampler)$", k):
                        pass
                    else:
                        job.update({k: v})
                for _width in data["width"]:
                    job.update({"width": _width})
                    for _height in data["height"]:
                        job.update({"height": _height})
                        for _cfg_scale in data["cfg_scale"]:
                            job.update({"cfg_scale": _cfg_scale})
                            for _steps in data["steps"]:
                                job.update({"steps": _steps})
                                for _sampler in data["sampler"]:
                                    for idx, name in enumerate(sd_samplers.samplers):
                                        if _sampler in name:
                                            job.update({"sampler_index": idx})
                                    jobs.append(job.copy())

        img_count = len(jobs) * p.n_iter
        batch_count = math.ceil(img_count / p.batch_size)
        print(f"Will process {img_count} images in {batch_count} batches.")

        state.job_count = batch_count

        images = []
        for i, job in enumerate(jobs):
            copy_p = copy.copy(p)
            state.job = f"{i + 1} out of {state.job_count}"
            for k, v in job.items():
                setattr(copy_p, k, v)

            proc = process_images(copy_p)
            images += proc.images

        return Processed(p, images, p.seed, "")
