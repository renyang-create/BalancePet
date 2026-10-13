# -*- coding: utf-8 -*-
"""
在桌面创建 Balance Pet 快捷方式（仅 Windows）。

要点：
    · 用 pythonw.exe 启动 —— 否则每次都会弹一个黑色控制台窗口
    · 顺便从宠物图生成 pet.ico 当图标

项目换位置后重新执行一次即可：

    python tools/make_shortcut.py
"""

import os
import subprocess
import sys
import tempfile

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PY = os.path.join(BASE_DIR, "main.py")
ASSETS = os.path.join(BASE_DIR, "assets")
ICO = os.path.join(ASSETS, "pet.ico")
SHORTCUT_NAME = "Balance Pet.lnk"


def make_icon():
    """把宠物图裁成正方形并生成多尺寸 .ico"""
    src = os.path.join(ASSETS, "pet_idle_static.png")
    if not os.path.exists(src):
        src = os.path.join(ASSETS, "pet.png")
    if not os.path.exists(src):
        print("[跳过] 找不到素材，无法生成图标")
        return False

    im = Image.open(src).convert("RGBA")
    bb = im.split()[3].getbbox()
    if bb:
        im = im.crop(bb)
    side = max(im.size)
    pad = int(side * 0.06)
    canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((canvas.width - im.width) // 2,
                                (canvas.height - im.height) // 2))
    canvas.resize((256, 256), Image.LANCZOS).save(
        ICO, format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("[OK] 图标 ->", ICO)
    return True


def pythonw_path():
    """优先 pythonw.exe（无控制台窗口）"""
    exe = sys.executable
    cand = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return cand if os.path.exists(cand) else exe


def desktop_dir():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$([Environment]::GetFolderPath('Desktop'))"],
            capture_output=True, text=True)
        path = (out.stdout or "").strip()
        if path and os.path.isdir(path):
            return path
    except OSError:
        pass
    return os.path.join(os.path.expanduser("~"), "Desktop")


def make_shortcut():
    lnk = os.path.join(desktop_dir(), SHORTCUT_NAME)
    script = f'''$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("{lnk}")
$lnk.TargetPath = "{pythonw_path()}"
$lnk.Arguments = '"{MAIN_PY}"'
$lnk.WorkingDirectory = "{BASE_DIR}"
$lnk.IconLocation = "{ICO}"
$lnk.Description = "Balance Pet - DeepSeek 余额桌宠"
$lnk.Save()
'''
    fd, path = tempfile.mkstemp(suffix=".ps1")
    os.close(fd)
    # 带 BOM 写，PowerShell 才认中文路径
    with open(path, "w", encoding="utf-8-sig") as fp:
        fp.write(script)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", path], capture_output=True, text=True)
        if r.returncode != 0:
            print("[失败]", (r.stderr or "").strip()[:400])
            return
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    print("[OK] 快捷方式 ->", lnk)


if __name__ == "__main__":
    make_icon()
    make_shortcut()
