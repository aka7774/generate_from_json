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
        directory = gr.Textbox(label="Prompts Directory", value="prompts", interactive=True)
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

        # webp出力機能
        webp_directory = None
        config_json = directory + "/config.json"
        if os.path.exists(config_json):
            f = open(config_json)
            data = json.load(f)

            if ("webp_directory" in data):
                webp_directory = data["webp_directory"]
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
                
        # prompts/json読み込み
        files = glob(directory + "/*.json")
        jobs = []
        for fn in files:
            if os.path.basename(fn) == "config.json":
                continue
            with open(fn) as f:
                data = json.load(f)
                job = dict()
                job.update({"name": os.path.splitext(os.path.basename(fn))[0]})

                # その他の項目
                for k, v in data.items():
                    a = ["width","height","cfg_scale","steps","sd_model_hash","clip_skip","sampler","eta","hypernet","hypernet_strength","ensd"]
                    if k not in a:
                        job.update({k: v})

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
                # pprint.pprint(result)
                for r in result:
                    i = 0
                    for k in data.keys():
                        if k in ["width","height","cfg_scale","steps","clip_skip","ensd"]:
                            job.update({k: int(r[i])})
                        elif k in ["hypernet_strength", "eta"]:
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

        # Hypernetをnameから引けるように準備しておく
        hs = {}
        for filename in hypernetwork.list_hypernetworks(cmd_opts.hypernetwork_dir).values():
            h = hypernetwork.Hypernetwork()
            h.load(filename)
            hs[h.name] = filename

        images = []
        for i, job in enumerate(jobs):
            copy_p = copy.copy(p)
            state.job = f"{i + 1} out of {state.job_count}"
            for k, v in job.items():
                match k:
                    case "name":
                        fn = v
                    case "sd_model_hash":
                        for c in sd_models.checkpoints_list.values():
                            if c.hash == v:
                                opts.sd_model_checkpoint = c.title
                        sd_models.reload_model_weights()
                    case "hypernet":
                        if v == "None":
                            shared.loaded_hypernetwork = None
                            continue
                        if shared.loaded_hypernetwork != None and shared.loaded_hypernetwork.name == v:
                            continue
                        for hn, hf in hs.items():
                            if hn == v:
                                shared.loaded_hypernetwork = hypernetwork.Hypernetwork()
                                shared.loaded_hypernetwork.load(hf)
                                break
                    case "hypernet_strength":
                        opts.sd_hypernetwork_strength = float(v)
                    case "ensd":
                        opts.eta_noise_seed_delta = v
                    case _:
                        setattr(copy_p, k, v)

            proc = process_images(copy_p)

            for image in proc.images:
                if webp_directory == None:
                    break
                image = image.convert("RGB")

                # webp upscale
                def upscale(image, scaler_index, resize, mode, resize_w, resize_h, crop):
                    upscaler = shared.sd_upscalers[scaler_index]
                    c = upscaler.scaler.upscale(image, resize, upscaler.data_path)
                    if mode == 1 and crop:
                        cropped = Image.new("RGB", (resize_w, resize_h))
                        cropped.paste(c, box=(resize_w // 2 - c.width // 2, resize_h // 2 - c.height // 2))
                        c = cropped

                    return c

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
                webp_dst = os.path.join(webp_directory, f"{fn}.webp")
                if os.path.exists(webp_dst):
                    image.save(os.path.join(webp_directory, f"{fn}-{float(time.time())}.webp"), quality=webp_quality)
                else:
                    image.save(webp_dst, quality=webp_quality)

            images += proc.images

        return Processed(p, images, p.seed, "")
