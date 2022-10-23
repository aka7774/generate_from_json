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
        def shift_attention(text, distance):
            re_attention_span = re.compile(r"([.\d]+)~([.\d]+)", re.X)
            def inject_value(distance, match_obj):
                start_weight = float(match_obj.group(1))
                end_weight = float(match_obj.group(2))
                return str(round(start_weight + (end_weight - start_weight) * distance, 6))

            res = re.sub(re_attention_span, lambda match_obj: inject_value(distance, match_obj), text)
            return res

        p.do_not_save_grid = True

        files = glob(directory + "/*.json")

        jobs = []
        for fn in files:
            with open(fn) as f:
                data = json.load(f)
                job = dict()

                # その他の項目
                for k, v in data.items():
                    a = ["width","height","cfg_scale","steps","sd_model_hash","clip_skip","sampler"]
                    if k not in a:
                        job.update({k: v})
                
                if (data["prompt_count"]):
                    c = data["prompt_count"]
                    pp = []
                    for i in range(c):
                        res = shift_attention(data["prompt"], float(i / (c - 1)))
                        pp.append(res)
                        if (res == data["prompt"]):
                            break
                    np = []
                    for i in range(c):
                        res = shift_attention(data["negative_prompt"], float(i / (c - 1)))
                        np.append(res)
                        if (res == data["negative_prompt"]):
                            break
                    data["prompt"] = pp
                    data["negative_prompt"] = np
                    del data["prompt_count"]

                tmp = []
                # 辞書のitemで回す
                for key, value in data.items():
                    if type(value) != list:
                        # valueがリストでないときはリストに変換
                        # リストの要素がstrでないときはstrに変換してtmpに突っ込む
                        tmp.append([str(data[key])] if data[key] != str else [data[key]])
                    else:
                        # valueがリスト
                        # valueの要素のsub_keyがstrでないときはstrに変換
                        tmp.append( [str(sub_key) if sub_key != str else sub_key 
                                                  for sub_key in value] )

                # *tmp でリストを展開して突っ込む ここで項目が1要素でもリストにしておかないと文字列のリストとみなされる
                result = list(itertools.product(*tmp, repeat=1))
                pprint.pprint(result)
                for r in result:
                    i = 0
                    for k in data.keys():
                        a = ["width","height","cfg_scale","steps","clip_skip"]
                        if k in a:
                            job.update({k: int(r[i])})
                        elif k == "sampler":
                            for idx, name in enumerate(sd_samplers.samplers):
                                if r[i] in name:
                                    job.update({"sampler_index": idx})
                        else:
                            job.update({k: r[i]})
                        i += 1
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
