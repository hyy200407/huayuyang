import pyautogui
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
import time

# Windows DPI 多屏幕坐标修复
import ctypes
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
except Exception:
    pass

# ====================== 全局控制变量 ======================
RUN_TASK = False            # 任务总开关
FAV_X = 0                   # 收藏按钮坐标 X
FAV_Y = 0                   # 收藏按钮坐标 Y
LIKE_X = 0                  # 视频区域坐标 X（点赞前点击此处确保焦点）
LIKE_Y = 0                  # 视频区域坐标 Y
SWITCH_INTERVAL = 3.0       # 视频切换间隔（秒）
MODE = "both"               # 运行模式: "like" / "favorite" / "both"
LISTEN_MOUSE_FLAG = False   # 鼠标坐标捕获开关
MOUSE_X = 0                 # 鼠标实时 X
MOUSE_Y = 0                 # 鼠标实时 Y
CAPTURE_TARGET = "like"     # 当前捕获目标: "like" / "favorite"
LOCK_COORD_CALLBACK = None  # 坐标锁定回调（GUI 注册）

# ====================== 全局键盘热键 ======================
# 注意：不使用 ESC（会退出抖音全屏）和 F12（会打开开发者工具）
# 改用 Ctrl+Shift+X 作为停止热键，不干扰浏览器和抖音
STOP_KEY_PRESSED = False    # Ctrl+Shift+X 组合键状态标记

def key_listener_thread():
    global RUN_TASK, LISTEN_MOUSE_FLAG, MOUSE_X, MOUSE_Y, CAPTURE_TARGET
    global STOP_KEY_PRESSED

    # 跟踪修饰键状态
    ctrl_down = False
    shift_down = False

    def on_press(key):
        global RUN_TASK, LISTEN_MOUSE_FLAG, MOUSE_X, MOUSE_Y
        nonlocal ctrl_down, shift_down

        # 追踪 Ctrl / Shift 状态
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_down = True
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            shift_down = True

        # Ctrl+Shift+X 强制停止（不干扰浏览器和抖音）
        try:
            if hasattr(key, 'char') and key.char == 'x' and ctrl_down and shift_down:
                RUN_TASK = False
                print("\n【Ctrl+Shift+X 热键触发】停止所有任务")
                return
        except Exception:
            pass

        # Enter 锁定坐标（追踪模式下，不触发页面点击）
        if key == keyboard.Key.enter and LISTEN_MOUSE_FLAG:
            LISTEN_MOUSE_FLAG = False
            print(f"\n【Enter键】{CAPTURE_TARGET} 坐标已锁定 X:{MOUSE_X} Y:{MOUSE_Y}")
            if LOCK_COORD_CALLBACK:
                LOCK_COORD_CALLBACK(CAPTURE_TARGET, MOUSE_X, MOUSE_Y)
            return

        # Q 取消坐标捕获
        try:
            if hasattr(key, 'char') and key.char == "q" and LISTEN_MOUSE_FLAG:
                LISTEN_MOUSE_FLAG = False
                print("\n【Q键】取消坐标追踪")
        except Exception:
            pass

    def on_release(key):
        nonlocal ctrl_down, shift_down
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_down = False
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            shift_down = False

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

# ====================== 全局鼠标监听（仅实时追踪位置） ======================
def mouse_listener_thread(update_coord_func):
    global MOUSE_X, MOUSE_Y
    def on_move(x, y):
        global MOUSE_X, MOUSE_Y
        MOUSE_X = x
        MOUSE_Y = y
        if LISTEN_MOUSE_FLAG:
            update_coord_func(x, y)

    from pynput import mouse
    m_listen = mouse.Listener(on_move=on_move)
    m_listen.daemon = True
    m_listen.start()

# ====================== 核心任务循环 ======================
def task_loop(mode, like_x, like_y, fav_x, fav_y, interval):
    global RUN_TASK
    count = 0
    while RUN_TASK:
        # ── ① 点赞：先点击视频区域确保焦点，再按 Z ──
        if mode in ("like", "both"):
            if like_x > 0 and like_y > 0:
                pyautogui.click(like_x, like_y)   # 点击视频区域，确保键盘焦点
                time.sleep(0.2)
            pyautogui.press("z")                   # 抖音网页版点赞快捷键
            time.sleep(0.15)

        # ── ② 收藏：鼠标点击收藏坐标 ──
        if mode in ("favorite", "both"):
            if fav_x > 0 and fav_y > 0:
                pyautogui.click(fav_x, fav_y)
            time.sleep(0.15)

        count += 1
        action_label = {"like": "点赞", "favorite": "收藏", "both": "点赞+收藏"}[mode]
        print(f"✓ 第 {count} 个作品 · {action_label}完成 · 等待 {interval}s 后切换")

        # ── ③ 等待切换间隔 ──
        elapsed = 0
        while RUN_TASK and elapsed < interval:
            time.sleep(0.1)
            elapsed += 0.1

        # ── ④ 切换到下一个作品：按下方向键↓ ──
        if RUN_TASK:
            pyautogui.press("down")
            time.sleep(0.3)

    print("✅ 任务循环已终止")

# ====================== 守护线程：Ctrl+Shift+X 兜底检测 ======================
def stop_key_daemon():
    """备用兜底：轮询检测 Ctrl+Shift+X 组合键（pynput 可能丢事件）"""
    global RUN_TASK
    while True:
        try:
            ctrl  = ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000  # Ctrl
            shift = ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000  # Shift
            x_key = ctypes.windll.user32.GetAsyncKeyState(0x58) & 0x8000  # X
            if ctrl and shift and x_key:
                RUN_TASK = False
        except Exception:
            pass
        time.sleep(0.3)

# ====================== GUI界面类 ======================
class DouyinAutoBot:

    def __init__(self, root):
        global LOCK_COORD_CALLBACK
        self.root = root
        self.root.title("✦ 抖音自动点赞收藏工具 Pro")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f2f5")
        self.root.attributes("-topmost", True)

        # 注册坐标锁定回调
        LOCK_COORD_CALLBACK = self._on_coord_lock

        # 自定义 ttk 样式
        self._setup_theme()

        # 绑定界面变量
        self.var_like_x = tk.StringVar(value="0")
        self.var_like_y = tk.StringVar(value="0")
        self.var_fav_x = tk.StringVar(value="0")
        self.var_fav_y = tk.StringVar(value="0")
        self.var_interval = tk.StringVar(value="3.0")
        self.var_mode = tk.StringVar(value="both")
        self.var_tip = tk.StringVar(value="程序就绪")

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        mouse_listener_thread(self.refresh_coord_display)

        # 初始窗口高度 + 初始卡片布局（默认 both）
        self.root.after(50, lambda: self._apply_mode_layout("both"))
        self.root.geometry("620x760")

    # ───────────────── 主题 ─────────────────
    def _setup_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        C_PRIMARY = "#4f6ef7"
        C_SUCCESS = "#22c55e"
        C_DANGER  = "#ef4444"
        C_DARK    = "#1e293b"
        C_SURFACE = "#ffffff"
        C_BG      = "#f0f2f5"

        style.configure("TFrame", background=C_BG)
        style.configure("Card.TLabelframe", background=C_SURFACE, borderwidth=0, relief="solid")
        style.configure("Card.TLabelframe.Label", background=C_SURFACE, foreground=C_DARK,
                        font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TLabel", background=C_SURFACE, foreground=C_DARK,
                        font=("Microsoft YaHei UI", 10))
        style.configure("Start.TButton", background=C_SUCCESS, foreground="#ffffff",
                        borderwidth=0, relief="flat", padding=(24, 10),
                        font=("Microsoft YaHei UI", 11, "bold"))
        style.map("Start.TButton", background=[("active", "#16a34a"), ("pressed", "#15803d")])
        style.configure("Stop.TButton", background=C_DANGER, foreground="#ffffff",
                        borderwidth=0, relief="flat", padding=(24, 10),
                        font=("Microsoft YaHei UI", 11, "bold"))
        style.map("Stop.TButton", background=[("active", "#dc2626"), ("pressed", "#b91c1c")])
        style.configure("Outline.TButton", background=C_SURFACE, foreground=C_PRIMARY,
                        borderwidth=1, relief="solid", padding=(18, 8),
                        font=("Microsoft YaHei UI", 10))
        style.map("Outline.TButton", background=[("active", "#eef2ff"), ("pressed", "#dbe4ff")])
        style.configure("TRadiobutton", background=C_SURFACE, foreground=C_DARK,
                        font=("Microsoft YaHei UI", 10))

    # ───────────────── 状态灯 ─────────────────
    def _draw_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(1, 1, 9, 9, fill=color, outline=color)

    def _set_status(self, text, color):
        self.var_tip.set(text)
        self._draw_dot(color)
        self.root.update_idletasks()

    # ───────────────── 模式切换：显示/隐藏坐标卡片 + 自适应窗口高度 ─────────────────
    def _apply_mode_layout(self, mode):
        """根据模式显示/隐藏卡片，并自动适配窗口高度"""
        if mode == "like":
            self.card_like.pack(fill="x", pady=(0, 10), before=self.card_interval)
            self.card_fav.pack_forget()
        elif mode == "favorite":
            self.card_like.pack_forget()
            self.card_fav.pack(fill="x", pady=(0, 10), before=self.card_interval)
        else:  # both
            self.card_like.pack(fill="x", pady=(0, 10), before=self.card_interval)
            self.card_fav.pack(fill="x", pady=(0, 10), before=self.card_interval)

        # 强制 tkinter 重新计算布局
        self.root.update_idletasks()
        # 取内容实际所需的高度（+10 余量避免底部被切）
        req_h = self.root.winfo_reqheight() + 10
        w = self.root.winfo_width()
        self.root.geometry(f"{w}x{req_h}")

    # ───────────────── 界面组件 ─────────────────
    def create_widgets(self):
        C_DARK    = "#1e293b"
        C_MUTED   = "#64748b"
        C_BG      = "#f0f2f5"
        C_SURFACE = "#ffffff"

        # ═══════════════ 顶部 Banner ═══════════════
        banner = tk.Frame(self.root, bg=C_SURFACE, height=62)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        tk.Frame(banner, bg="#fe2c55", width=4, height=62).pack(side="left", fill="y")
        title_area = tk.Frame(banner, bg=C_SURFACE)
        title_area.pack(side="left", fill="both", expand=True, padx=(16, 0))
        tk.Label(title_area, text="🎵 抖音自动点赞收藏工具 Pro",
                 font=("Microsoft YaHei UI", 15, "bold"),
                 fg="#1e293b", bg=C_SURFACE).pack(anchor="w", pady=(10, 0))
        tk.Label(title_area, text="点击视频区获取焦点 → Z键点赞 → 点击收藏按钮 → ↓键切视频",
                 font=("Microsoft YaHei UI", 9),
                 fg="#94a3b8", bg=C_SURFACE).pack(anchor="w")

        # ═══════════════ 主内容区 ═══════════════
        content = tk.Frame(self.root, bg=C_BG)
        content.pack(fill="both", expand=True, padx=16, pady=(12, 8))

        # ── 卡片①：运行模式 ──
        card0 = ttk.LabelFrame(content, text="   🎯  运行模式", style="Card.TLabelframe")
        card0.pack(fill="x", pady=(0, 10))
        inner0 = tk.Frame(card0, bg=C_SURFACE)
        inner0.pack(fill="x", padx=16, pady=(6, 14))
        tk.Label(inner0, text="选择对每个作品执行的操作类型（切换后页面自动伸缩适配）",
                 font=("Microsoft YaHei UI", 9), fg=C_MUTED, bg=C_SURFACE).pack(anchor="w", pady=(0, 10))
        mode_row = tk.Frame(inner0, bg=C_SURFACE)
        mode_row.pack(fill="x")
        ttk.Radiobutton(mode_row, text="👍  仅点赞", variable=self.var_mode, value="like",
                        command=lambda: self._apply_mode_layout("like")).pack(side="left", padx=(0, 24))
        ttk.Radiobutton(mode_row, text="⭐  仅收藏", variable=self.var_mode, value="favorite",
                        command=lambda: self._apply_mode_layout("favorite")).pack(side="left", padx=(0, 24))
        ttk.Radiobutton(mode_row, text="👍+⭐  同时点赞和收藏", variable=self.var_mode, value="both",
                        command=lambda: self._apply_mode_layout("both")).pack(side="left")

        # ── 卡片②：点赞区域坐标（like / both 时显示）──
        self.card_like = ttk.LabelFrame(content, text="   👍  点赞区域坐标（确保键盘焦点）", style="Card.TLabelframe")
        inner_like = tk.Frame(self.card_like, bg=C_SURFACE)
        inner_like.pack(fill="x", padx=16, pady=(6, 14))
        tk.Label(inner_like, text="点击「追踪点赞区」→ 鼠标移到视频画面任意位置 → 按 Enter 锁定",
                 font=("Microsoft YaHei UI", 9), fg=C_MUTED, bg=C_SURFACE).pack(anchor="w", pady=(0, 10))
        lr = tk.Frame(inner_like, bg=C_SURFACE)
        lr.pack(fill="x")
        ttk.Button(lr, text="🎯 追踪点赞区", style="Outline.TButton",
                   command=self.start_capture_like).pack(side="left", padx=(0, 16))
        tk.Label(lr, text="X", font=("Microsoft YaHei UI", 10, "bold"), fg=C_DARK, bg=C_SURFACE).pack(side="left")
        ttk.Entry(lr, textvariable=self.var_like_x, width=8, font=("Consolas", 11)).pack(side="left", padx=(4, 12))
        tk.Label(lr, text="Y", font=("Microsoft YaHei UI", 10, "bold"), fg=C_DARK, bg=C_SURFACE).pack(side="left")
        ttk.Entry(lr, textvariable=self.var_like_y, width=8, font=("Consolas", 11)).pack(side="left", padx=(4, 0))

        # ── 卡片③：收藏按钮坐标（favorite / both 时显示）──
        self.card_fav = ttk.LabelFrame(content, text="   ⭐  收藏按钮坐标", style="Card.TLabelframe")
        inner_fav = tk.Frame(self.card_fav, bg=C_SURFACE)
        inner_fav.pack(fill="x", padx=16, pady=(6, 14))
        tk.Label(inner_fav, text="点击「追踪收藏区」→ 鼠标移到收藏⭐按钮 → 按 Enter 锁定（不触发点击）",
                 font=("Microsoft YaHei UI", 9), fg=C_MUTED, bg=C_SURFACE).pack(anchor="w", pady=(0, 10))
        fr = tk.Frame(inner_fav, bg=C_SURFACE)
        fr.pack(fill="x")
        ttk.Button(fr, text="🎯 追踪收藏区", style="Outline.TButton",
                   command=self.start_capture_fav).pack(side="left", padx=(0, 16))
        tk.Label(fr, text="X", font=("Microsoft YaHei UI", 10, "bold"), fg=C_DARK, bg=C_SURFACE).pack(side="left")
        ttk.Entry(fr, textvariable=self.var_fav_x, width=8, font=("Consolas", 11)).pack(side="left", padx=(4, 12))
        tk.Label(fr, text="Y", font=("Microsoft YaHei UI", 10, "bold"), fg=C_DARK, bg=C_SURFACE).pack(side="left")
        ttk.Entry(fr, textvariable=self.var_fav_y, width=8, font=("Consolas", 11)).pack(side="left", padx=(4, 0))

        # ── 卡片④：切换间隔 ──
        self.card_interval = ttk.LabelFrame(content, text="   ⚙️  视频切换间隔", style="Card.TLabelframe")
        self.card_interval.pack(fill="x", pady=(0, 10))
        inner2 = tk.Frame(self.card_interval, bg=C_SURFACE)
        inner2.pack(fill="x", padx=16, pady=(6, 14))
        tk.Label(inner2, text="每个作品停留的时间，足够看完 + 点赞收藏后再切下一个",
                 font=("Microsoft YaHei UI", 9), fg=C_MUTED, bg=C_SURFACE).pack(anchor="w", pady=(0, 10))
        iv_row = tk.Frame(inner2, bg=C_SURFACE)
        iv_row.pack(fill="x")
        tk.Label(iv_row, text="切换间隔", font=("Microsoft YaHei UI", 10, "bold"),
                 fg=C_DARK, bg=C_SURFACE).pack(side="left")
        ttk.Entry(iv_row, textvariable=self.var_interval, width=10,
                  font=("Consolas", 12)).pack(side="left", padx=(8, 4))
        tk.Label(iv_row, text="秒 / 作品", font=("Microsoft YaHei UI", 9),
                 fg=C_MUTED, bg=C_SURFACE).pack(side="left")

        # ── 卡片⑤：任务控制 ──
        card3 = ttk.LabelFrame(content, text="   🎮  任务控制", style="Card.TLabelframe")
        card3.pack(fill="x", pady=(0, 10))
        inner3 = tk.Frame(card3, bg=C_SURFACE)
        inner3.pack(fill="x", padx=16, pady=(6, 14))
        btn_row = tk.Frame(inner3, bg=C_SURFACE)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="▶  启动任务", style="Start.TButton",
                   command=self.run_task).pack(side="left", padx=(0, 12))
        ttk.Button(btn_row, text="■  立即停止  (Ctrl+Shift+X)", style="Stop.TButton",
                   command=self.stop_task).pack(side="left")

        # ── 状态栏 ──
        sf = tk.Frame(content, bg="#f8fafc", highlightbackground="#e2e8f0",
                      highlightthickness=1, padx=14, pady=10)
        sf.pack(fill="x", pady=(0, 12))
        self.status_dot = tk.Canvas(sf, width=10, height=10, bg="#f8fafc", highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8))
        self._draw_dot("#94a3b8")
        tk.Label(sf, textvariable=self.var_tip, font=("Microsoft YaHei UI", 10, "bold"),
                 fg="#334155", bg="#f8fafc").pack(side="left")

        # ── 操作指南 ──
        guide = ttk.LabelFrame(content, text="   📖  操作指南 & 快捷键", style="Card.TLabelframe")
        guide.pack(fill="x")
        inner_g = tk.Frame(guide, bg=C_SURFACE)
        inner_g.pack(fill="x", padx=16, pady=(6, 12))
        tips = [
            ("①", "打开作品",     "在浏览器打开抖音博主首页，点开任意一个作品"),
            ("②", "捕获坐标",     "按模式追踪点赞区/收藏区 → 鼠标移至目标 → Enter 锁定"),
            ("③", "选择模式",     "勾选「仅点赞」「仅收藏」或「同时点赞和收藏」"),
            ("④", "启动任务",     "点击启动，程序点击视频区→Z键点赞→点收藏→等间隔→↓切下一个"),
            ("Enter","锁定坐标",   "追踪模式下按 Enter 锁定当前鼠标位置（不触发页面点击）"),
            ("Ctrl+","Shift+X",   "全局停止热键，不干扰抖音全屏(ESC)和开发者工具(F12)"),
            ("Q",   "取消追踪",    "追踪模式下按 Q 取消坐标捕获"),
        ]
        for i, (key, title, desc) in enumerate(tips):
            col = "#f1f5f9" if i % 2 == 0 else C_SURFACE
            row = tk.Frame(inner_g, bg=col)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=key, font=("Consolas", 10, "bold"),
                     fg="#fe2c55", bg=col, width=6, anchor="w").pack(side="left", padx=(8, 0))
            tk.Label(row, text=title, font=("Microsoft YaHei UI", 10, "bold"),
                     fg=C_DARK, bg=col, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=("Microsoft YaHei UI", 9),
                     fg=C_MUTED, bg=col, anchor="w").pack(side="left")

        # ── 底部 ──
        footer = tk.Frame(self.root, bg=C_BG)
        footer.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(footer, text="Made with ❤️  ·  Douyin Auto Bot Pro  v2.0",
                 font=("Microsoft YaHei UI", 8), fg="#c0c8d4", bg=C_BG).pack(side="right")

        # 初始显示：默认 "both" → 两张坐标卡片都显示
        self.card_like.pack(fill="x", pady=(0, 10), before=self.card_interval)
        self.card_fav.pack(fill="x", pady=(0, 10), before=self.card_interval)

    # ───────────────── 回调方法 ─────────────────

    def refresh_coord_display(self, x, y):
        """鼠标移动时只刷新当前追踪目标的坐标显示"""
        global CAPTURE_TARGET
        if CAPTURE_TARGET == "like":
            self.var_like_x.set(str(x))
            self.var_like_y.set(str(y))
        else:
            self.var_fav_x.set(str(x))
            self.var_fav_y.set(str(y))
        self.root.update_idletasks()

    def _on_coord_lock(self, target, x, y):
        """Enter 键触发：锁定坐标到对应目标（由键盘监听器回调）"""
        if target == "like":
            self.var_like_x.set(str(x))
            self.var_like_y.set(str(y))
            self._set_status(f"✅ 点赞区域坐标锁定成功 X:{x} Y:{y}", "#fe2c55")
        else:
            self.var_fav_x.set(str(x))
            self.var_fav_y.set(str(y))
            self._set_status(f"✅ 收藏按钮坐标锁定成功 X:{x} Y:{y}", "#f59e0b")

    def start_capture_like(self):
        global LISTEN_MOUSE_FLAG, RUN_TASK, CAPTURE_TARGET
        if RUN_TASK:
            messagebox.showwarning("警告", "请先停止正在运行的任务！")
            return
        CAPTURE_TARGET = "like"
        LISTEN_MOUSE_FLAG = True
        self._set_status("🖱️ 追踪点赞区：移动鼠标到视频画面上 → 按 Enter 锁定", "#f59e0b")

    def start_capture_fav(self):
        global LISTEN_MOUSE_FLAG, RUN_TASK, CAPTURE_TARGET
        if RUN_TASK:
            messagebox.showwarning("警告", "请先停止正在运行的任务！")
            return
        CAPTURE_TARGET = "favorite"
        LISTEN_MOUSE_FLAG = True
        self._set_status("🖱️ 追踪收藏区：移动鼠标到收藏⭐按钮上 → 按 Enter 锁定", "#f59e0b")

    def run_task(self):
        global RUN_TASK, LIKE_X, LIKE_Y, FAV_X, FAV_Y, SWITCH_INTERVAL, MODE
        if LISTEN_MOUSE_FLAG:
            messagebox.showwarning("提示", "请先按 Enter 锁定坐标，关闭追踪后再启动！")
            return

        mode = self.var_mode.get()
        try:
            interval = float(self.var_interval.get())
            like_x = int(self.var_like_x.get())
            like_y = int(self.var_like_y.get())
            fav_x = int(self.var_fav_x.get())
            fav_y = int(self.var_fav_y.get())
        except ValueError:
            messagebox.showerror("输入错误", "坐标、间隔必须填写数字！")
            return

        if interval < 1.0:
            messagebox.showerror("限制", "切换间隔不能小于 1 秒，防止风控")
            return

        # 点赞模式需要视频区域坐标
        if mode in ("like", "both") and (like_x == 0 and like_y == 0):
            messagebox.showwarning("提示", "点赞模式需要先捕获「点赞区域坐标」（视频画面上的任意点）！")
            return

        # 收藏模式需要收藏按钮坐标
        if mode in ("favorite", "both") and (fav_x == 0 and fav_y == 0):
            messagebox.showwarning("提示", "收藏模式需要先捕获「收藏按钮坐标」！")
            return

        if RUN_TASK:
            messagebox.showinfo("提示", "任务正在运行中，无需重复启动")
            return

        LIKE_X = like_x
        LIKE_Y = like_y
        FAV_X = fav_x
        FAV_Y = fav_y
        SWITCH_INTERVAL = interval
        MODE = mode
        RUN_TASK = True

        mode_label = {"like": "仅点赞", "favorite": "仅收藏", "both": "点赞+收藏"}[mode]
        self._set_status(f"🚀 任务运行中 · 模式: {mode_label} · 间隔: {interval}s", "#22c55e")
        threading.Thread(target=task_loop, args=(mode, like_x, like_y, fav_x, fav_y, interval), daemon=True).start()

    def stop_task(self):
        global RUN_TASK
        RUN_TASK = False
        self._set_status("🛑 已手动停止任务", "#ef4444")

    def on_window_close(self):
        global RUN_TASK
        RUN_TASK = False
        self.root.destroy()


if __name__ == "__main__":
    threading.Thread(target=key_listener_thread, daemon=True).start()
    threading.Thread(target=stop_key_daemon, daemon=True).start()
    root = tk.Tk()
    app = DouyinAutoBot(root)
    root.mainloop()
