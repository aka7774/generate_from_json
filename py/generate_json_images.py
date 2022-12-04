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

from . import const
from .extra_outputs import extra_outputs

# Hypernetをnameから引けるように準備しておく
hs = {}
def cache_hypernetwork_names():
    for filename in hypernetwork.list_hypernetworks(cmd_opts.hypernetwork_dir).values():
        h = hypernetwork.Hypernetwork()
        h.load(filename)
        hs[h.name] = filename
        del h

def shift_attention(text, distance):
    re_attention_span = re.compile(r"([.\d]+)~([.\d]+)", re.X)
    def inject_value(distance, match_obj):
        start_weight = float(match_obj.group(1))
        end_weight = float(match_obj.group(2))
        return str(round(start_weight + (end_weight - start_weight) * distance, 6))

    res = re.sub(re_attention_span, lambda match_obj: inject_value(distance, match_obj), text)
    return res

def generate_json_images(p):
    files = glob(const.JSON_DIR + "/*.json")
    jobs = []
    for fn in files:
        with open(fn) as f:
            data = json.load(f)
            job = dict()
            job.update({"name": os.path.splitext(os.path.basename(fn))[0]})

            for k, v in data.items():
                # aは複数指定に対応させる項目
                a = ["width","height","cfg_scale","steps","sd_model_hash","clip_skip","sampler","eta","hypernet","hypernet_strength","ensd","subseed","subseed_strength","seed_resize_from_w","seed_resize_from_h","denoising_strength"]
                # a以外はそのままstrで渡してみる
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
                    if k in ["width","height","cfg_scale","steps","clip_skip","ensd","subseed","seed_resize_from_w","seed_resize_from_h"]:
                        job.update({k: int(r[i])})
                    elif k in ["hypernet_strength", "eta","subseed_strength","denoising_strength"]:
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

    cache_hypernetwork_names()

    images = []
    for i, job in enumerate(jobs):
        copy_p = copy.copy(p)
        state.job = f"{i + 1} out of {state.job_count}"

        # use default values
        opts.eta_noise_seed_delta = 0
        opts.sd_hypernetwork_strength = 1.0
        opts.eta_ddim = 0.0
        opts.eta_ancestral = 1.0

        for k, v in job.items():
            if k == "name":
                fn = v
            elif k == "sd_model_hash":
                for c in sd_models.checkpoints_list.values():
                    if c.hash == v:
                        opts.sd_model_checkpoint = c.title
                sd_models.reload_model_weights()
            elif k == "hypernet":
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
            elif k == "hypernet_strength":
                opts.sd_hypernetwork_strength = float(v)
            elif k == "ensd":
                opts.eta_noise_seed_delta = v
            else:
                setattr(copy_p, k, v)

        proc = process_images(copy_p)
        extra_outputs(fn, proc.images)
        images += proc.images

    return images
