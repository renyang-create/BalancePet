# -*- coding: utf-8 -*-
"""
Balance Pet —— 一只显示 DeepSeek 账户余额的桌面宠物。

交互：
    · 左键点击：互动台词 + 一段"整体微动"（呼吸 / 浮沉）
    · 左键拖拽：移动位置
    · 右键菜单：立即刷新余额 / 设置 API Key / 关于 / 退出

关于密钥：
    代码里没有任何密钥。API Key 只从同目录的 .env 文件读取，
    读不到时再退回系统环境变量 DEEPSEEK_API_KEY。
"""

import os
import queue
import sys
import threading
import time
import tkinter as tk
import traceback

import customtkinter as ctk
import requests
from PIL import Image

# --------------------------------------------------------------------------- #
# 路径与常量
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ERROR_LOG = os.path.join(BASE_DIR, "pet_error.log")

BALANCE_URL = "https://api.deepseek.com/user/balance"

STATIC_IMAGE = os.path.join(ASSETS_DIR, "pet_idle_static.png")
FRAME_DIR = os.path.join(ASSETS_DIR, "pet_frames")
PET_SIZE = (176, 172)          # 桌面上显示的尺寸（逻辑像素）

FRAME_MS = 85                  # 动画每帧停留毫秒（一轮约 1.9 秒）
ANIM_LOOPS = 2                 # 点一次播几轮
CLICK_TEXT = "最喜欢大肥鱼惹"

WIN_W, WIN_H = 250, 232        # 窗口尺寸（逻辑像素）
TRANSPARENT_KEY = "#000001"    # 被抠成透明的"幕布色"

ENV_TEMPLATE = """# DeepSeek 余额桌宠配置
# 填入你的 DeepSeek API Key（sk- 开头）。也可以改用系统环境变量 DEEPSEEK_API_KEY。
DEEPSEEK_API_KEY=
# 余额自动刷新间隔（秒），不要小于 15
REFRESH_INTERVAL=60
"""


# --------------------------------------------------------------------------- #
# .env 读写
# --------------------------------------------------------------------------- #
def read_env():
    """读取 .env；文件不存在就用模板默认值"""
    cfg = {"DEEPSEEK_API_KEY": "", "REFRESH_INTERVAL": "60"}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    cfg[key.strip()] = val.strip().strip('"').strip("'")
        except OSError:
            pass
    return cfg


def write_env(cfg):
    """把配置写回 .env（保持固定的文件结构，方便用户手改）"""
    lines = [
        "# DeepSeek 余额桌宠配置",
        "# 填入你的 DeepSeek API Key（sk- 开头）。也可以改用系统环境变量 DEEPSEEK_API_KEY。",
        "DEEPSEEK_API_KEY=" + (cfg.get("DEEPSEEK_API_KEY") or ""),
        "# 余额自动刷新间隔（秒），不要小于 15",
        "REFRESH_INTERVAL=" + str(cfg.get("REFRESH_INTERVAL") or 60),
        "",
    ]
    try:
        with open(ENV_FILE, "w", encoding="utf-8") as fp:
            fp.write("\n".join(lines))
    except OSError:
        pass


def get_api_key(cfg):
    """优先 .env，其次系统环境变量"""
    key = (cfg.get("DEEPSEEK_API_KEY") or "").strip()
    if not key:
        key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    return key


def get_interval(cfg):
    try:
        return max(15, int(float(cfg.get("REFRESH_INTERVAL") or 60)))
    except (TypeError, ValueError):
        return 60


# --------------------------------------------------------------------------- #
# DeepSeek 余额接口
# --------------------------------------------------------------------------- #
def fetch_balance(api_key):
    """
    查询账户余额。

    返回 (气泡第一行, 气泡第二行)
    接口：GET https://api.deepseek.com/user/balance
    鉴权：Authorization: Bearer <API_KEY>
    响应：{"is_available": true,
           "balance_infos": [{"currency": "CNY", "total_balance": "110.00",
                              "granted_balance": "10.00", "topped_up_balance": "100.00"}]}
    """
    key = (api_key or "").strip()
    if not key:
        return "还没设置 API Key", "右键 → 设置 API Key"

    try:
        resp = requests.get(
            BALANCE_URL,
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            timeout=10,
        )
    except requests.RequestException as exc:
        return "网络异常，稍后重试", f"({type(exc).__name__})"

    if resp.status_code == 401:
        return "API Key 无效或已过期", "右键 → 设置 API Key"
    if resp.status_code != 200:
        return f"请求失败 HTTP {resp.status_code}", "右键 → 立即刷新余额"

    try:
        data = resp.json() or {}
    except ValueError:
        return "返回内容不是合法 JSON", "右键 → 立即刷新余额"

    infos = data.get("balance_infos") or []
    if not infos:
        return "接口没返回余额信息", "右键 → 立即刷新余额"

    info = infos[0]
    currency = (info.get("currency") or "CNY").upper()
    symbol = "¥" if currency == "CNY" else f"{currency} "
    available = "可用" if data.get("is_available") else "不可用"

    line1 = f"余额 {symbol}{info.get('total_balance', '?')}  {currency}"
    line2 = (f"{available} · 赠金 {symbol}{info.get('granted_balance', '?')}"
             f" · 充值 {symbol}{info.get('topped_up_balance', '?')}")
    return line1, line2


# --------------------------------------------------------------------------- #
# 桌宠
# --------------------------------------------------------------------------- #
class BalancePet(ctk.CTkToplevel):
    def __init__(self, root):
        super().__init__(root)
        # 注意：属性名不要叫 self._root —— tkinter 内部有 _root() 方法，撞名会让异常上报本身也崩掉
        self.app_root = root
        self.cfg = read_env()

        self.title("Balance Pet · DeepSeek 余额")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.overrideredirect(True)                 # 无边框
        self.attributes("-topmost", True)           # 全局置顶
        # 注意：Windows 上 -alpha<1 会让 -transparentcolor 失效，整窗变成半透明灰纱，所以不要用 alpha
        self.attributes("-transparentcolor", TRANSPARENT_KEY)
        # 窗口底色也要等于抠色，否则气泡以外会是一块不透明灰底
        self.configure(fg_color=TRANSPARENT_KEY)

        # 拖拽状态
        self.x = None
        self.y = None
        self._dragging = False

        # 气泡
        self.label_balance = ctk.CTkLabel(
            self, text="加载中…", font=("Microsoft YaHei", 13),
            fg_color="#222222", text_color="white", corner_radius=12, justify="center")
        self.label_balance.pack(pady=(8, 4))

        # 宠物图片（找不到素材时退回 emoji，保证不至于开不起来）
        self.pet_image = None
        if os.path.exists(STATIC_IMAGE):
            img = Image.open(STATIC_IMAGE).convert("RGBA")
            self.pet_image = ctk.CTkImage(light_image=img, dark_image=img, size=PET_SIZE)
            self.fish_label = ctk.CTkLabel(self, text="", image=self.pet_image,
                                           fg_color=TRANSPARENT_KEY)
        else:
            self.fish_label = ctk.CTkLabel(self, text="🐟", font=("", 90),
                                           fg_color=TRANSPARENT_KEY)
        self.fish_label.pack()

        # 动画帧
        self.frames = []
        if os.path.isdir(FRAME_DIR):
            for name in sorted(os.listdir(FRAME_DIR)):
                if name.lower().endswith(".png"):
                    frame = Image.open(os.path.join(FRAME_DIR, name)).convert("RGBA")
                    self.frames.append(ctk.CTkImage(light_image=frame, dark_image=frame,
                                                    size=PET_SIZE))
        self._anim_job = None
        self._anim_step = 0

        # 事件绑定
        # 注意：<Button-1> 就是 <ButtonPress-1> 的别名，不能拿它当"点击"用，
        #       否则每次拖动都会被判成一次点击。点击判定放在 <ButtonRelease-1> 里。
        self.fish_label.bind("<ButtonPress-1>", self.start_move)
        self.fish_label.bind("<B1-Motion>", self.do_move)
        self.fish_label.bind("<ButtonRelease-1>", self.stop_move)
        self.fish_label.bind("<Button-3>", self.popup_menu)

        self._build_menu()

        # 余额数据先丢进队列，由主线程取出来刷界面（Tk 不是线程安全的）
        self.queue = queue.Queue()
        self._wake = threading.Event()
        self.thread = threading.Thread(target=self.refresh_loop, daemon=True)
        self.thread.start()
        self.after(200, self.apply_balance)
        self.after(120, self.place_bottom_right)

    def place_bottom_right(self):
        """
        默认停在屏幕右下角。

        坑：customtkinter 会按 DPI 缩放窗口 —— geometry 里的宽高是"逻辑像素"，
        位置却是"实际像素"。而且窗口没映射前 winfo_width() 拿不到最终值，
        所以必须等窗口真正映射之后再量、再定位。
        """
        try:
            self.update_idletasks()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            w, h = self.winfo_width(), self.winfo_height()
            self.geometry(f"+{max(0, sw - w - 60)}+{max(0, sh - h - 120)}")
        except Exception:
            pass

    # ------------------------------ 右键菜单 ------------------------------ #
    def _build_menu(self):
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="立即刷新余额", command=self.refresh_now)
        self.menu.add_command(label="设置 API Key…", command=self.set_api_key)
        self.menu.add_separator()
        self.menu.add_command(label="关于", command=self.show_about)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.quit_app)

    def popup_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def quit_app(self):
        try:
            self.app_root.destroy()
        except Exception:
            sys.exit(0)

    # ------------------------------ 拖拽 / 点击 ------------------------------ #
    def start_move(self, event):
        # 记下鼠标在窗口内的落点，后面按根坐标反推窗口位置，
        # 避免"位移累加"导致窗口跑飞
        self.x = event.x_root - self.winfo_x()
        self.y = event.y_root - self.winfo_y()
        self._dragging = False

    def do_move(self, event):
        if self.x is None:
            return
        nx = event.x_root - self.x
        ny = event.y_root - self.y
        if abs(nx - self.winfo_x()) > 3 or abs(ny - self.winfo_y()) > 3:
            self._dragging = True
        self.geometry(f"+{nx}+{ny}")

    def stop_move(self, event):
        dragged = self._dragging
        self.x = None
        self.y = None
        self._dragging = False
        if not dragged:                     # 拖过就不算点击
            self.on_click(event)

    def on_click(self, event=None):
        self.label_balance.configure(text=CLICK_TEXT)
        self.play_anim()

    # ------------------------------- 动画 ------------------------------- #
    def play_anim(self):
        """播 ANIM_LOOPS 轮微动，播完回到静止图"""
        if not self.frames:
            return
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        self._anim_step = 0
        self._anim_tick()

    def _anim_tick(self):
        total = len(self.frames) * ANIM_LOOPS
        if self._anim_step >= total:
            self._anim_step = 0
            self._anim_job = None
            if self.pet_image is not None:
                self.fish_label.configure(image=self.pet_image)
            return
        self.fish_label.configure(image=self.frames[self._anim_step % len(self.frames)])
        self._anim_step += 1
        self._anim_job = self.after(FRAME_MS, self._anim_tick)

    # ------------------------------- 余额 ------------------------------- #
    def refresh_now(self):
        self.label_balance.configure(text="刷新中…")
        self._wake.set()

    def refresh_loop(self):
        while True:
            try:
                result = fetch_balance(get_api_key(self.cfg))
            except Exception as exc:                     # 兜底，别让线程死掉
                result = ("获取失败", type(exc).__name__)
            # 只往队列里塞数据，绝对不要在子线程里碰控件：
            # 一旦主线程没停在 mainloop 上就会抛 RuntimeError，
            # "main thread is not in main loop"，刷新线程当场死掉
            self.queue.put(result)
            self._wake.wait(get_interval(self.cfg))
            self._wake.clear()

    def apply_balance(self):
        try:
            while True:
                line1, line2 = self.queue.get_nowait()
                self.label_balance.configure(text=f"{line1}\n{line2}")
        except queue.Empty:
            pass
        self.after(500, self.apply_balance)

    # ---------------------------- 设置 / 关于 ---------------------------- #
    def set_api_key(self):
        try:
            dlg = ctk.CTkInputDialog(text="粘贴 DeepSeek API Key（sk- 开头）",
                                     title="设置 API Key")
            try:
                dlg.attributes("-topmost", True)
            except Exception:
                pass
            key = dlg.get_input()
        except Exception:
            return
        if key is None:
            return
        self.cfg["DEEPSEEK_API_KEY"] = key.strip()
        write_env(self.cfg)
        self.label_balance.configure(text="已保存到 .env，正在刷新…")
        self.refresh_now()

    def show_about(self):
        key = get_api_key(self.cfg)
        masked = f"{key[:6]}…{key[-4:]}" if len(key) > 12 else ("未设置" if not key else "已设置")
        info = (
            "Balance Pet · DeepSeek 余额桌宠\n\n"
            "左键点击：互动台词 + 整体微动\n"
            "左键拖拽：移动位置\n"
            "右键菜单：刷新 / 设置 Key / 退出\n\n"
            f"当前 Key：{masked}\n"
            f"刷新间隔：{get_interval(self.cfg)} 秒\n"
            f"配置文件：.env\n"
            f"接口：{BALANCE_URL}"
        )
        try:
            win = ctk.CTkToplevel(self)
            win.title("关于")
            win.geometry(f"380x270+{self.winfo_x()}+{max(0, self.winfo_y() - 220)}")
            win.attributes("-topmost", True)
            ctk.CTkLabel(win, text="关于", font=("Microsoft YaHei", 16, "bold")).pack(pady=(14, 6))
            ctk.CTkLabel(win, text=info, justify="left",
                         font=("Microsoft YaHei", 11)).pack(padx=18, anchor="w")
            ctk.CTkButton(win, text="知道啦", width=110, command=win.destroy).pack(pady=12)
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def main():
    root = ctk.CTk()
    root.withdraw()

    def log_exception(exc, val, tb):
        """用 pythonw 启动时没有控制台，异常统一写进日志文件"""
        try:
            with open(ERROR_LOG, "a", encoding="utf-8") as fp:
                fp.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}]\n")
                traceback.print_exception(exc, val, tb, file=fp)
        except OSError:
            pass

    root.report_callback_exception = log_exception
    # 必须保留引用：否则实例会被垃圾回收，窗口随之销毁，mainloop 会立刻返回
    app = BalancePet(root)
    root.mainloop()
    return app


if __name__ == "__main__":
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w", encoding="utf-8") as fp:
            fp.write(ENV_TEMPLATE)
        print("已生成 .env，请填入你的 DeepSeek API Key 后重新启动。")
    try:
        main()
    except Exception:
        with open(ERROR_LOG, "a", encoding="utf-8") as fp:
            fp.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 启动失败\n")
            traceback.print_exc(file=fp)
        raise
