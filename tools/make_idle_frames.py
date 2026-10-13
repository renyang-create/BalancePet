# -*- coding: utf-8 -*-
"""
生成桌宠的"整体微动"动画帧 -> assets/pet_frames/f00.png ...

原理：整张图做刚体变换（等比缩放 + 平移），没有任何局部变形。所以：
    · 不可能断脖子 / 撕裂 —— 整块一起动，不存在接缝
    · 不可能多出五官     —— 一个像素都不重绘，只是把原图整体缩放平移

首帧（u=0）和末帧（u→1）都恰好回到原始姿态，因此：
    · 循环播放无缝
    · "静止图 ↔ 动画"切换不会跳（静止图直接用第 0 帧）

想换宠物形象：把 assets/pet.png 换成你自己的透明 PNG，再执行本脚本。

    python tools/make_idle_frames.py
"""

import math
import os

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE_DIR, "assets")
SRC = os.path.join(ASSETS, "pet.png")
OUT = os.path.join(ASSETS, "pet_frames")
STATIC = os.path.join(ASSETS, "pet_idle_static.png")

N_FRAMES = 22        # 一轮帧数
MAX_SIDE = 340       # 输出长边
PAD_X = 24           # 左右留白（给平移余量）
PAD_TOP = 46         # 顶部留白（缩放是往上长的，不留会切头）
PAD_BOTTOM = 10

BREATH_Y = 0.025     # 纵向鼓起幅度（±2.5%）
BREATH_X = 0.015     # 横向收窄幅度
BOB = 3.0            # 吸气上浮像素
SWAY = 1.5           # 左右轻摇像素


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"找不到素材：{SRC}")

    src = Image.open(SRC).convert("RGBA")
    w, h = src.size

    # 先铺一张带留白的画布，把原图贴进去；锚点取"原图底部中心"
    canvas = Image.new("RGBA", (w + PAD_X * 2, h + PAD_TOP + PAD_BOTTOM), (0, 0, 0, 0))
    canvas.alpha_composite(src, (PAD_X, PAD_TOP))
    cw, ch = canvas.size
    ax, ay = cw / 2.0, PAD_TOP + h

    frames = []
    for i in range(N_FRAMES):
        u = i / N_FRAMES
        breathe = math.sin(2.0 * math.pi * u)          # 0 -> 1 -> 0 -> -1 -> 0
        sy = 1.0 + BREATH_Y * breathe
        sx = 1.0 - BREATH_X * breathe
        ty = -BOB * breathe
        tx = SWAY * math.sin(2.0 * math.pi * u + math.pi / 2.0)

        # transform 接收的是"输出 -> 输入"的逆向映射：src = anchor + S⁻¹(dest - anchor - T)
        inv = (1.0 / sx, 0.0, ax - (ax + tx) / sx,
               0.0, 1.0 / sy, ay - (ay + ty) / sy)
        frames.append(canvas.transform(canvas.size, Image.AFFINE, inv,
                                       resample=Image.BICUBIC))

    # 用第 0 帧（= 原始姿态）的内容盒统一切片，四周留出容纳起伏的余量
    bb = frames[0].split()[3].getbbox()
    margin = int(max(BOB, SWAY) + abs(BREATH_Y) * h / 2) + 6
    box = (max(0, bb[0] - margin), max(0, bb[1] - margin),
           min(cw, bb[2] + margin), min(ch, bb[3] + margin))
    scale = MAX_SIDE / max(box[2] - box[0], box[3] - box[1])
    size = (round((box[2] - box[0]) * scale), round((box[3] - box[1]) * scale))

    os.makedirs(OUT, exist_ok=True)
    for n, f in enumerate(frames):
        f.crop(box).resize(size, Image.LANCZOS).save(os.path.join(OUT, f"f{n:02d}.png"))
    Image.open(os.path.join(OUT, "f00.png")).save(STATIC)

    print(f"[OK] {len(frames)} 帧 -> {OUT}")
    print(f"[OK] 静止图 -> {STATIC}  {size}")


if __name__ == "__main__":
    main()
