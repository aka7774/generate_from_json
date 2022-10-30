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

import modules.scripts as scripts
import gradio as gr

from modules.processing import Processed, process_images
from PIL import Image
from modules.shared import opts, cmd_opts, state
from modules import sd_samplers, shared
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
            with gr.Column(variant='panel'):
                with gr.Group():
                    directory = gr.Textbox(label="Prompts Directory", value="prompts", interactive=True)
                    open_directory = gr.Button("Open Prompts Directory")
                    open_directory.click(
                        fn=open_folder,
                        inputs=directory,
                        outputs=[],
                    )

                with gr.Group():
                    webp_check = gr.Checkbox(label="Output webp with upscale", value=False)
                    webp_quality_txt = gr.Textbox(label="Quality", value="75")
                    webp_directory = gr.Textbox(label="webp Directory", value="outputs_webp", interactive=True)
                    open_webp_directory = gr.Button("Open webp Directory")
                    open_webp_directory.click(
                        fn=open_folder,
                        inputs=webp_directory,
                        outputs=[],
                    )
                    with gr.Tabs(elem_id="extras_resize_mode"):
                        with gr.Group():
                            resize_check = gr.Checkbox(label="Enable upscale", value=False)
                        with gr.TabItem('Scale by'):
                            upscaling_resize = gr.Slider(minimum=1.0, maximum=4.0, step=0.05, label="Resize", value=2)
                        with gr.TabItem('Scale to'):
                            with gr.Group():
                                with gr.Row():
                                    upscaling_resize_w = gr.Number(label="Width", value=512, precision=0)
                                    upscaling_resize_h = gr.Number(label="Height", value=512, precision=0)
                                upscaling_crop = gr.Checkbox(label='Crop to fit', value=True)
                    with gr.Group():
                        extras_upscaler_1 = gr.Radio(label='Upscaler 1', elem_id="extras_upscaler_1", choices=[x.name for x in shared.sd_upscalers], value=shared.sd_upscalers[0].name, type="index")

        return [directory, open_directory, webp_check, webp_quality_txt, webp_directory, open_webp_directory,
                             resize_check, upscaling_resize, upscaling_resize_w, upscaling_resize_h, upscaling_crop, extras_upscaler_1]

    def on_show(self, directory, open_directory, webp_check, webp_quality_txt, webp_directory, open_webp_directory,
                     resize_check, upscaling_resize, upscaling_resize_w, upscaling_resize_h, upscaling_crop, extras_upscaler_1):
        return [gr.Textbox.update(visible=True),
                gr.Button.update(visible=True),
                ]

    def run(self, p, directory, open_directory, webp_check, webp_quality_txt, webp_directory, open_webp_directory,
                     resize_check, upscaling_resize, upscaling_resize_w, upscaling_resize_h, upscaling_crop, extras_upscaler_1):

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
                    a = ["width","height","cfg_scale","steps","sd_model_hash","clip_skip","sampler","eta","Hypernet","ENSD"]
                    if k not in a:
                        job.update({k: v})

                if ("upscaler" in data):
                    extras_upscaler_1 = data["upscaler"]
                    del data["upscaler"]
                    if (data["upscaling_resize"]):
                        upscaling_resize = float(data["upscaling_resize"])
                        del data["upscaling_resize"]
                    if ("upscaling_resize_w" in data):
                        upscaling_resize_w = int(data["upscaling_resize_w"])
                        upscaling_resize_h = int(data["upscaling_resize_h"])
                        del data["upscaling_resize_w"]
                        del data["upscaling_resize_h"]
                    if ("upscaling_crop" in data):
                        upscaling_crop = int(data["upscaling_crop"])
                        del data["upscaling_crop"]

                if ("webp_quality" in data):
                    webp_quality = int(data["webp_quality"])
                    del data["webp_quality"]

                if ("prompt_count" in data):
                    c = data["prompt_count"]
                    if c > 1:
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
                        if k in ["width","height","cfg_scale","steps","clip_skip","ENSD"]:
                            job.update({k: int(r[i])})
                        elif k in ["eta"]:
                            job.update({k: float(r[i])})
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

            for image in proc.images:
                if webp_check == False:
                    break
                image = image.convert("RGB")

                def upscale(image, scaler_index, resize, mode, resize_w, resize_h, crop):
                    upscaler = shared.sd_upscalers[scaler_index]
                    c = upscaler.scaler.upscale(image, resize, upscaler.data_path)
                    if mode == 1 and crop:
                        cropped = Image.new("RGB", (resize_w, resize_h))
                        cropped.paste(c, box=(resize_w // 2 - c.width // 2, resize_h // 2 - c.height // 2))
                        c = cropped

                    return c

                if resize_check:
                    if upscaling_resize == 1.0:
                        resize_mode = 1
                        upscaling_resize = max(upscaling_resize_w/image.width, upscaling_resize_h/image.height)
                    else:
                        resize_mode = 0
                        upscaling_resize_w = image.width * upscaling_resize
                        upscaling_resize_h = image.height * upscaling_resize

                    res = upscale(image, extras_upscaler_1, upscaling_resize, resize_mode, upscaling_resize_w, upscaling_resize_h, upscaling_crop)
                    image = res

                home_path = os.path.dirname(os.path.dirname(fn))
                image.save(os.path.join(home_path, 'output_webp', f"{os.path.splitext(os.path.basename(fn))[0]}-{float(time.time())}.webp"), quality=int(webp_quality_txt))

            images += proc.images

        return Processed(p, images, p.seed, "")
