"""
老六 Chat - AI 桌面助手
豆包风格输入栏 · 红色主题 · 主对话+历史会话
蓝模式「跳跳」— 视觉+键鼠操控
"""
import tkinter as tk
from tkinter import font, messagebox, simpledialog
import subprocess
import threading
import queue
import os
import sys
import re
import time
import sqlite3
import socket
import json
import base64
import traceback
from datetime import datetime, timedelta
import tempfile
import mimetypes

# ===== 高 DPI =====
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ===== 拖放支持 (Windows, 零依赖) =====
try:
    import ctypes
    from ctypes import wintypes
    _WS_EX_ACCEPTFILES = 0x10
    _WM_DROPFILES = 0x0233
    _GWL_EXSTYLE = -20

    def _enable_drag_drop(hwnd: int):
        """为指定窗口句柄启用文件拖放"""
        exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, exstyle | _WS_EX_ACCEPTFILES)

    _DND_ENABLED = True
except:
    _DND_ENABLED = False

# ===== 配置（基于脚本位置，不再硬编码） =====
WORK = os.path.dirname(os.path.abspath(__file__))
OPENCLAW = os.path.join(WORK, r"node_modules\.bin\openclaw.cmd")
NODE = os.path.join(WORK, "nodejs")
DATA_DIR = os.path.join(WORK, "chat-data")
DB_PATH = os.path.join(DATA_DIR, "sessions.db")
BLUE_DIR = os.path.join(WORK, "blue-mode")
MAIN_ID = "__main__"
MAIN_TTL = 4
os.makedirs(DATA_DIR, exist_ok=True)

os.environ["NODE_HOME"] = NODE
os.environ["OPENCLAW_HOME"] = WORK
os.environ["PATH"] = NODE + ";" + os.path.join(WORK, r"node_modules\.bin") + ";" + os.environ.get("PATH", "")

# 加载蓝模式模块
sys.path.insert(0, BLUE_DIR)
try:
    import themes
    THEME_OK = True
except Exception as e:
    THEME_OK = False
    print(f"Warning: themes module not loaded: {e}")

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except:
    PIL_OK = False

# ===== 主题加载 =====
if THEME_OK:
    RED = themes.RED
    BLUE = themes.BLUE
    MODE_META = themes.MODE_META
else:
    # 回退：硬编码红色主题
    RED = {}
    BLUE = {}
    MODE_META = {}

# 从主题取色（运行时切换）
def T(key):
    """从当前主题取色，带回退"""
    if THEME_OK and hasattr(T, "_theme"):
        return T._theme.get(key, RED.get(key, "#000000"))
    return RED.get(key, "#000000") if RED else "#000000"

T._theme = RED if RED else {}

# ===== 数据库 =====
class DB:
    def __init__(self, path):
        self.c = sqlite3.connect(path, check_same_thread=False)
        self.c.execute("PRAGMA journal_mode=WAL")
        self.c.execute("CREATE TABLE IF NOT EXISTS s (id TEXT PRIMARY KEY, title TEXT, main INT DEFAULT 0, ts TEXT)")
        self.c.execute("CREATE TABLE IF NOT EXISTS m (id INTEGER PRIMARY KEY AUTOINCREMENT, sid TEXT, role TEXT, content TEXT, ts TEXT)")
        self.c.commit()
        self._fix_main()

    def _fix_main(self):
        now = datetime.now().isoformat()
        self.c.execute("INSERT OR IGNORE INTO s (id,title,main,ts) VALUES (?,?,1,?)", (MAIN_ID, "主对话", now))
        cut = (datetime.now() - timedelta(days=MAIN_TTL)).isoformat()
        self.c.execute("DELETE FROM m WHERE sid=? AND ts < ?", (MAIN_ID, cut))
        self.c.commit()

    def new_hist(self, title):
        sid = "h-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        now = datetime.now().isoformat()
        self.c.execute("INSERT INTO s (id,title,main,ts) VALUES (?,?,0,?)", (sid, title, now))
        self.c.commit()
        return sid

    def list(self):
        rows = self.c.execute("SELECT id,title,main,ts FROM s ORDER BY main DESC, ts DESC").fetchall()
        return [{"id":r[0],"title":r[1],"main":bool(r[2]),"ts":r[3]} for r in rows]

    def msgs(self, sid):
        return [{"role":r[0],"content":r[1]} for r in
                self.c.execute("SELECT role,content FROM m WHERE sid=? ORDER BY id ASC",(sid,)).fetchall()]

    def add(self, sid, role, content):
        now = datetime.now().isoformat()
        self.c.execute("INSERT INTO m (sid,role,content,ts) VALUES (?,?,?,?)", (sid,role,content,now))
        self.c.execute("UPDATE s SET ts=? WHERE id=?", (now,sid))
        self.c.commit()

    def rename(self, sid, title):
        self.c.execute("UPDATE s SET title=? WHERE id=?", (title,sid))
        self.c.commit()

    def delete(self, sid):
        if sid == MAIN_ID: return
        self.c.execute("DELETE FROM m WHERE sid=?", (sid,))
        self.c.execute("DELETE FROM s WHERE id=?", (sid,))
        self.c.commit()

    def ctx(self, sid, n=20):
        rows = self.c.execute("SELECT role,content FROM m WHERE sid=? ORDER BY id DESC LIMIT ?",(sid,n)).fetchall()
        return [{"role":r[0],"content":r[1]} for r in reversed(rows)]


# ===== 主题色初始化（从 RED 主题加载）=====
_t = RED if RED else {}
BG0 = _t.get("BG0","#2e1e20"); BG1 = _t.get("BG1","#362426")
BG2 = _t.get("BG2","#322022"); BG3 = _t.get("BG3","#392628")
BG4 = _t.get("BG4","#3f2a2c"); BG5 = _t.get("BG5","#442a2c")
BG6 = _t.get("BG6","#382426"); BG7 = _t.get("BG7","#472a2c")
BG8 = _t.get("BG8","#3e2426"); CB = _t.get("CB","#543234")
CF = _t.get("CF","#c84040"); AC = _t.get("AC","#c84040")
AH = _t.get("AH","#dd4a3c"); AL = _t.get("AL","#ec6a60")
T1 = _t.get("T1","#f2e4e0"); T2 = _t.get("T2","#c4a4a4")
T3 = _t.get("T3","#947c7c"); GR = _t.get("GR","#4caf50")
YW = _t.get("YW","#f0a030"); RD = _t.get("RD","#f04040")
INP_BG = _t.get("INP_BG","#f5f0f0"); INP_FG = _t.get("INP_FG","#1a0a0a")
INP_BDR = _t.get("INP_BDR","#c84040"); BAR_BG = _t.get("BAR_BG","#100808")
BAR_HINT = _t.get("BAR_HINT","#704848")
SW = 220


# ===== 应用 =====
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("老六 Chat")
        self.root.geometry("900x680")
        self.root.minsize(560, 440)
        self.root.configure(bg=BG0)

        # 设置窗口图标
        try:
            icon_path = os.path.join(WORK, "app-icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

        self.db = DB(DB_PATH)
        self.mq = queue.Queue()
        self.busy = False
        self.sid = MAIN_ID
        self.imgs = []
        self._hist = []
        self._gw_ok = False
        self.mode = "red"  # red | blue
        self.theme = RED if RED else {}  # 当前主题字典
        self._tw = []  # theme-widgets: 需要换肤的 widget
        self._pending_files = []  # 待发送的文件列表 [{"path":..., "type":"image"|"file"}]
        self._file_labels = []   # 附件标签 widget

        self._fonts()
        self._ui()
        self._load()
        self._gw_thread()

        # 蓝模式：启动温故调度器
        if THEME_OK:
            try:
                import wengu
                self.wengu = wengu.get_instance()
            except:
                self.wengu = None

    def _fonts(self):
        self.fn = font.Font(family="Microsoft YaHei", size=11)
        self.fs = font.Font(family="Microsoft YaHei", size=9)
        self.fb = font.Font(family="Microsoft YaHei", size=11, weight="bold")
        self.ft = font.Font(family="Microsoft YaHei", size=12, weight="bold")
        self.fc = font.Font(family="Cascadia Code", size=9)
        self.fx = font.Font(family="Microsoft YaHei", size=8)
        self.f15 = font.Font(family="Microsoft YaHei", size=15, weight="bold")

    # ================== UI 骨架 ==================

    def _ui(self):
        p = tk.PanedWindow(self.root, bg=BG0, bd=0, sashwidth=1, sashrelief=tk.FLAT)
        p.pack(fill=tk.BOTH, expand=True)

        self.sb = tk.Frame(p, bg=BG2, width=SW)
        p.add(self.sb, minsize=50)
        self._sidebar()

        self.ma = tk.Frame(p, bg=BG1)
        p.add(self.ma, minsize=320)
        self._main()

    def _sidebar(self):
        s = self.sb

        # Logo
        lf = tk.Frame(s, bg=BG2, height=66)
        lf.pack(fill=tk.X, pady=(14,4)); lf.pack_propagate(False)
        lc = tk.Canvas(lf, width=40, height=40, bg=BG2, highlightthickness=0)
        lc.place(x=12, y=12)
        self._logo(lc)
        tk.Label(lf, text="老六 Chat", fg=T1, bg=BG2, font=self.ft).place(x=58,y=12)
        tk.Label(lf, text="SHIREN9527", fg=T3, bg=BG2, font=self.fx).place(x=58,y=36)

        tk.Frame(s, bg=CB, height=1).pack(fill=tk.X, padx=14, pady=(6,8))

        # 状态灯
        sf = tk.Frame(s, bg=BG2)
        sf.pack(fill=tk.X, padx=14)
        self.sd = tk.Canvas(sf, width=7, height=7, bg=BG2, highlightthickness=0)
        self.sd.pack(side=tk.LEFT, padx=(0,6))
        self._si = self.sd.create_oval(0,0,7,7,fill=RD,outline="")
        self.sl = tk.Label(sf, text="检测...", fg=T3, bg=BG2, font=self.fx)
        self.sl.pack(side=tk.LEFT)

        tk.Frame(s, bg=CB, height=1).pack(fill=tk.X, padx=14, pady=10)

        # 主对话
        tk.Label(s, text="⭐ 主对话", fg=T2, bg=BG2, font=self.fx, anchor="w", padx=14).pack(fill=tk.X)
        tk.Label(s, text=f"  每{MAIN_TTL}天自动清理", fg=T3, bg=BG2, font=self.fx, anchor="w", padx=14).pack(fill=tk.X, pady=(0,2))

        self.mf = tk.Frame(s, bg=BG2)
        self.mf.pack(fill=tk.X, padx=8, pady=(2,2))
        self.mb = tk.Label(self.mf, text="  主对话", fg=AL, bg=BG7, font=self.fs, anchor="w", padx=6, pady=7, cursor="hand2")
        self.mb.pack(fill=tk.X)
        self.mb.bind("<Button-1>", lambda e: self._to_main())

        tk.Frame(s, bg=CB, height=1).pack(fill=tk.X, padx=14, pady=10)

        # 历史会话
        hh = tk.Frame(s, bg=BG2)
        hh.pack(fill=tk.X, padx=14, pady=(0,4))
        tk.Label(hh, text="💬 历史会话", fg=T2, bg=BG2, font=self.fx).pack(side=tk.LEFT)
        tk.Label(hh, text="永久保留", fg=T3, bg=BG2, font=self.fx).pack(side=tk.RIGHT)

        nb = tk.Button(s, text="＋ 新建会话", bg=AC, fg="white", font=self.fs, borderwidth=0,
                      cursor="hand2", padx=10, pady=5, activebackground=AH, activeforeground="white",
                      command=self._new_hist)
        nb.pack(fill=tk.X, padx=14, pady=(4,6))

        self.hc = tk.Frame(s, bg=BG2)
        self.hc.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        tk.Frame(s, bg=CB, height=1).pack(fill=tk.X, padx=14, pady=(4,4))

        for em,lb,cmd in [("🗑️","清屏",self._cls)]:
            b = tk.Button(s, text=f"  {em}  {lb}", bg=BG2, fg=T2, font=self.fx, anchor="w",
                         borderwidth=0, cursor="hand2", padx=8, pady=5,
                         activebackground=BG8, activeforeground=AL)
            b.pack(fill=tk.X, padx=10)
            b.configure(command=cmd)
            self._tw.append(("btn", b, {"bg":BG2,"fg":T2,"activebackground":BG8,"activeforeground":AL}))

        tk.Frame(s, bg=CB, height=1).pack(fill=tk.X, padx=14, pady=(4,4))

        # ---- 模式切换按钮 ----
        self.mode_btn = tk.Button(s, text="🔵 切换跳跳", bg=AC, fg="white", font=self.fs,
                                  borderwidth=0, cursor="hand2", padx=10, pady=6,
                                  activebackground=AH, activeforeground="white",
                                  command=self._toggle_mode)
        self.mode_btn.pack(fill=tk.X, padx=14, pady=(2,2))

        # ---- 设置面板（可展开/收起）----
        self._settings_expanded = False
        self.settings_btn = tk.Button(s, text="⚙ 设置 API", bg=BG2, fg=T2, font=self.fx,
                                      borderwidth=0, cursor="hand2", padx=8, pady=4,
                                      activebackground=BG8, activeforeground=AL,
                                      command=self._toggle_settings_panel)
        self.settings_btn.pack(fill=tk.X, padx=14, pady=(0,2))

        # 设置面板容器（初始隐藏）
        self._settings_panel = tk.Frame(s, bg=BG3, padx=8, pady=6)

        tk.Label(self._settings_panel, text="API 地址", fg=T2, bg=BG3, font=self.fx, anchor="w").pack(fill=tk.X)
        self._api_url_entry = tk.Entry(self._settings_panel, font=self.fx, bg=BG4, fg=T1,
                                        relief=tk.FLAT, bd=3, insertbackground=AL, width=20)
        self._api_url_entry.pack(fill=tk.X, pady=(1,5))

        tk.Label(self._settings_panel, text="API Key", fg=T2, bg=BG3, font=self.fx, anchor="w").pack(fill=tk.X)
        key_row = tk.Frame(self._settings_panel, bg=BG3)
        key_row.pack(fill=tk.X, pady=(1,5))
        self._api_key_entry = tk.Entry(key_row, font=self.fx, bg=BG4, fg=T1,
                                        relief=tk.FLAT, bd=3, insertbackground=AL, width=16, show="•")
        self._api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._show_key_btn = tk.Button(key_row, text="👁", bg=BG4, fg=T2, font=self.fx,
                                        borderwidth=0, cursor="hand2", padx=4,
                                        activebackground=BG8,
                                        command=lambda: self._toggle_key_visibility())
        self._show_key_btn.pack(side=tk.RIGHT, padx=(4,0))

        tk.Label(self._settings_panel, text="模型", fg=T2, bg=BG3, font=self.fx, anchor="w").pack(fill=tk.X)
        model_row = tk.Frame(self._settings_panel, bg=BG3)
        model_row.pack(fill=tk.X, pady=(1,5))
        self._model_var = tk.StringVar(value="deepseek-v4-flash")
        self._model_combo = tk.OptionMenu(model_row, self._model_var,
                                           "deepseek-v4-flash", "deepseek-v4-pro",
                                           "deepseek-chat", "gpt-4o", "claude-sonnet-5",
                                           command=lambda v: None)
        self._model_combo.configure(bg=BG4, fg=T1, font=self.fx, relief=tk.FLAT,
                                     activebackground=BG8, activeforeground=T1,
                                     highlightthickness=0, borderwidth=0)
        self._model_combo["menu"].configure(bg=BG4, fg=T1, font=self.fx,
                                             activebackground=BG8, activeforeground=AL, borderwidth=0)
        self._model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(0,0))

        btn_row = tk.Frame(self._settings_panel, bg=BG3)
        btn_row.pack(fill=tk.X, pady=(4,0))
        tk.Button(btn_row, text="💾 保存", bg=AC, fg="white", font=self.fx,
                  borderwidth=0, cursor="hand2", padx=8, pady=3,
                  activebackground=AH, activeforeground="white",
                  command=self._save_inline_settings).pack(side=tk.LEFT)
        tk.Button(btn_row, text="更多", bg=BG4, fg=T2, font=self.fx,
                  borderwidth=0, cursor="hand2", padx=6, pady=3,
                  activebackground=BG8, activeforeground=AL,
                  command=self._open_settings).pack(side=tk.RIGHT)

        # 面板不立即 pack — 点击⚙后才展开

        tk.Frame(s, bg=CB, height=1).pack(fill=tk.X, padx=14, pady=(4,4))
        self.model_label = tk.Label(s, text="DeepSeek V4 Flash", fg=T3, bg=BG2, font=self.fx)
        self.model_label.pack(pady=(0,6))

    def _logo(self, c):
        c.create_oval(10,15,30,37,fill=AC,outline="")
        c.create_oval(12,3,28,22,fill=AH,outline="")
        c.create_oval(15,5,20,11,fill="white",outline="")
        c.create_oval(22,5,27,11,fill="white",outline="")
        c.create_oval(17,7,19,9,fill=BG0,outline="")
        c.create_oval(24,7,26,9,fill=BG0,outline="")
        c.create_line(4,17,10,24,fill=AC,width=3,capstyle=tk.ROUND)
        c.create_arc(0,13,12,27,start=50,extent=200,style="arc",outline=AL,width=2)
        c.create_line(28,24,34,17,fill=AC,width=3,capstyle=tk.ROUND)
        c.create_arc(26,13,38,27,start=-70,extent=200,style="arc",outline=AL,width=2)
        c.create_line(14,3,8,-4,fill=AL,width=1)
        c.create_line(24,3,30,-4,fill=AL,width=1)

    def _main(self):
        # ============ 底部输入栏（先 pack，保证优先占据空间）============
        tk.Frame(self.ma, bg=CB, height=2).pack(fill=tk.X, side=tk.BOTTOM)

        bar = tk.Frame(self.ma, bg=BAR_BG, height=110)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        # ---- 提示文字（输入框上方） ----
        hint = tk.Label(bar, text="输入消息 Enter 发送 · Shift+Enter 换行 · /model /apikey /config 切换配置", fg=BAR_HINT, bg=BAR_BG, font=self.fx)
        hint.pack(pady=(6,0))

        # ---- 输入行（圆角输入框） ----
        input_row = tk.Frame(bar, bg=BAR_BG, height=50)
        input_row.pack(fill=tk.X, padx=20, pady=(4,0))
        input_row.pack_propagate(False)

        # 圆角输入框：Canvas 绘制圆角边框 + Text widget 置于其上
        R = 14  # 圆角半径
        self._inp_frame = tk.Frame(input_row, bg=BAR_BG)
        self._inp_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 10))

        # Canvas 边框层
        self._inp_canvas = tk.Canvas(self._inp_frame, bg=BAR_BG, highlightthickness=0)
        self._inp_canvas.pack(fill=tk.BOTH, expand=True)

        # 输入框（白色背景，置于 Canvas 内）
        self.inp = tk.Text(self._inp_frame, wrap=tk.WORD,
                          bg=INP_BG, fg=INP_FG, font=self.fn,
                          padx=16, pady=10,
                          borderwidth=0, highlightthickness=0,
                          insertbackground=AC, insertwidth=3,
                          height=2, relief=tk.FLAT)
        self.inp.place(x=3, y=3, relwidth=1.0, relheight=1.0, width=-6, height=-6)

        # 绑定 resize 以重绘圆角
        def _draw_rounded(e=None):
            c = self._inp_canvas
            w = c.winfo_width()
            h = c.winfo_height()
            if w < 20 or h < 20:
                return
            r = R
            c.delete("rnd")
            # 四个角
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=INP_BDR, outline="", tags="rnd")
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=INP_BDR, outline="", tags="rnd")
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=INP_BDR, outline="", tags="rnd")
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=INP_BDR, outline="", tags="rnd")
            # 四个边
            c.create_rectangle(r, 0, w-r, h, fill=INP_BDR, outline="", tags="rnd")
            c.create_rectangle(0, r, w, h-r, fill=INP_BDR, outline="", tags="rnd")
            c.tag_lower("rnd")
        self._inp_canvas.bind("<Configure>", _draw_rounded)
        self.root.after(100, _draw_rounded)

        # ---- 圆形发送按钮 ----
        SZ = 42
        self.btn_c = tk.Canvas(input_row, width=SZ, height=SZ,
                                bg=BAR_BG, highlightthickness=0, cursor="hand2")
        self.btn_c.pack(side=tk.RIGHT)
        self._bc = self.btn_c.create_oval(0, 0, SZ, SZ, fill=AC, outline="", width=0)
        self._ba = self.btn_c.create_text(SZ/2, SZ/2, text="↑", fill="white",
                                           font=font.Font(family="Microsoft YaHei", size=18, weight="bold"),
                                           anchor="center")
        self.btn_c.bind("<Button-1>", lambda e: self._send())
        self.btn_c.bind("<Enter>", lambda e: self.btn_c.itemconfig(self._bc, fill=AH))
        self.btn_c.bind("<Leave>", lambda e: (self.btn_c.itemconfig(self._bc, fill=AC) if not self.busy else None))

        # ---- 📷 看屏幕按钮 ----
        self.btn_v = tk.Canvas(input_row, width=36, height=36,
                                bg=BAR_BG, highlightthickness=0, cursor="hand2")
        self.btn_v.pack(side=tk.RIGHT, padx=(0, 8))
        self._bv = self.btn_v.create_oval(0, 0, 36, 36, fill="#5a3040", outline="", width=0)
        self._bva = self.btn_v.create_text(18, 18, text="📷", fill="white",
                                            font=font.Font(family="Microsoft YaHei", size=14),
                                            anchor="center")
        self.btn_v.bind("<Button-1>", lambda e: self._shot_and_see())
        self.btn_v.bind("<Enter>", lambda e: self.btn_v.itemconfig(self._bv, fill="#7a4050"))
        self.btn_v.bind("<Leave>", lambda e: (self.btn_v.itemconfig(self._bv, fill="#5a3040") if not self.busy else None))

        # ---- 📎 选择文件按钮 ----
        self.btn_a = tk.Canvas(input_row, width=36, height=36,
                                bg=BAR_BG, highlightthickness=0, cursor="hand2")
        self.btn_a.pack(side=tk.RIGHT, padx=(0, 8))
        self._ba_bg = self.btn_a.create_oval(0, 0, 36, 36, fill="#40405a", outline="", width=0)
        self._ba_txt = self.btn_a.create_text(18, 18, text="📎", fill="white",
                                               font=font.Font(family="Microsoft YaHei", size=14),
                                               anchor="center")
        self.btn_a.bind("<Button-1>", lambda e: self._select_files())
        self.btn_a.bind("<Enter>", lambda e: self.btn_a.itemconfig(self._ba_bg, fill="#50506a"))
        self.btn_a.bind("<Leave>", lambda e: (self.btn_a.itemconfig(self._ba_bg, fill="#40405a") if not self.busy else None))

        # ---- 附件标签行（输入框上方）----
        self._attach_row = tk.Frame(bar, bg=BAR_BG, height=24)
        self._attach_row.pack(fill=tk.X, padx=20, pady=(2, 0))
        self._attach_row.pack_propagate(False)
        # 默认隐藏
        self._attach_row.pack_forget()

        # ---- 聊天区（填充剩余空间） ----
        chat_frame = tk.Frame(self.ma, bg=BG1)
        chat_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self.ca = tk.Text(chat_frame, wrap=tk.WORD, bg=BG1, fg=T1, font=self.fn,
                         padx=24, pady=14, borderwidth=0, highlightthickness=0,
                         insertbackground=T1, state=tk.DISABLED,
                         spacing2=2, spacing3=6)
        self.ca.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.ca.bind("<Button-1>", lambda e: self._focus_inp())

        sb = tk.Scrollbar(chat_frame, command=self.ca.yview, bg=BG1, troughcolor=BG3,
                         activebackground=AC, width=8)
        sb.pack(fill=tk.Y, side=tk.RIGHT)
        self.ca.configure(yscrollcommand=sb.set)
        self._tags()
        self.ca.bind("<MouseWheel>", lambda e: self.ca.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ---- 快捷键 ----
        self.inp.bind("<Return>", lambda e: self._send())
        self.inp.bind("<Shift-Return>", lambda e: self._nl())
        self.root.bind("<Escape>", lambda e: self._focus_inp())
        self.inp.bind("<Control-v>", lambda e: self._paste_clipboard(e))
        self.inp.bind("<Control-V>", lambda e: self._paste_clipboard(e))

        # ---- 拖放支持 ----
        if _DND_ENABLED:
            self.root.after(300, self._setup_drag_drop)

        # ---- 强制焦点 ----
        self.root.after(200, self._focus_inp)
        self.root.after(500, self._focus_inp)

    def _tags(self):
        ca = self.ca
        ca.tag_configure("ub", background=BG5, lmargin1=70, lmargin2=70, rmargin=20, spacing1=14, spacing3=4)
        ca.tag_configure("ul", foreground=AL, font=self.fs, lmargin1=82, lmargin2=82)
        ca.tag_configure("ab", background=BG6, lmargin1=20, lmargin2=20, rmargin=70, spacing1=14, spacing3=4)
        ca.tag_configure("al", foreground=AC, font=self.fs, lmargin1=32, lmargin2=32)
        ca.tag_configure("sy", foreground=T3, font=self.fx, justify="center", spacing1=8, spacing3=4)
        ca.tag_configure("er", foreground="#f06060", font=self.fs, lmargin1=32, lmargin2=32)
        ca.tag_configure("bo", font=self.fb)
        ca.tag_configure("cd", foreground=AL, font=self.fc, background="#0c0606",
                        lmargin1=32, lmargin2=32, spacing1=6, spacing3=6)
        ca.tag_configure("lk", foreground="#f5a0a0", font=self.fn, underline=True)
        ca.tag_configure("ip", foreground=T3, font=self.fx)

    # ================== 输入框 ==================

    # ================== 文件/图片处理 ==================

    def _setup_drag_drop(self):
        """为窗口启用 Windows 原生文件拖放"""
        try:
            hwnd = self.root.winfo_id()
            _enable_drag_drop(hwnd)
            # 使用 Tk 的 client 协议拦截 WM_DROPFILES
            self.root.createcommand("tk_win", self._on_drag_drop)
        except:
            pass

    def _on_drag_drop(self, *args):
        """处理 Windows 拖放文件事件"""
        try:
            # 检测到拖放时，通过文件名参数处理
            if len(args) >= 2 and args[0] == "drop":
                files_str = args[1] if len(args) > 1 else ""
                for f in files_str.split():
                    f = f.strip('"').strip("'")
                    if os.path.isfile(f):
                        self._add_attachment(f)
        except:
            pass

    def _select_files(self):
        """📎 按钮：打开文件选择对话框"""
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            title="选择文件或图片",
            filetypes=[
                ("所有支持的文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.txt;*.py;*.md;*.pdf;*.json;*.csv;*.log"),
                ("图片", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"),
                ("文本文件", "*.txt;*.py;*.md;*.json;*.csv;*.log"),
                ("PDF", "*.pdf"),
                ("所有文件", "*.*"),
            ]
        )
        for p in paths:
            if os.path.isfile(p):
                self._add_attachment(p)

    def _paste_clipboard(self, event=None):
        """Ctrl+V 检测剪贴板图片，有图片则作为附件，没有则正常粘贴文本"""
        try:
            from PIL import ImageGrab
            # 尝试读取剪贴板图片
            img = ImageGrab.grabclipboard()
            if img is not None:
                # 有图片，保存为临时文件并附加
                tmp = os.path.join(tempfile.gettempdir(), f"clipboard_{int(time.time())}.png")
                img.save(tmp, "PNG")
                self._add_attachment(tmp)
                return "break"  # 阻止默认粘贴行为
            elif isinstance(img, list):
                # 剪贴板有文件列表
                for f in img:
                    if os.path.isfile(f):
                        self._add_attachment(f)
                return "break"
        except:
            pass
        # 无图片，正常粘贴文本
        return None

    def _add_attachment(self, path: str):
        """添加一个附件到待发送列表"""
        if not os.path.exists(path):
            return
        ext = os.path.splitext(path)[1].lower()
        ftype = "image" if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp") else "file"

        # 避免重复添加
        if any(f["path"] == path for f in self._pending_files):
            return

        self._pending_files.append({"path": path, "type": ftype})

        # 显示附件标签
        self._attach_row.pack(fill=tk.X, padx=20, pady=(2, 0), before=self._inp_frame.master)

        name = os.path.basename(path)
        emoji = "🖼" if ftype == "image" else "📄"
        max_name = name[:18] + "…" if len(name) > 18 else name
        lbl = tk.Label(self._attach_row, text=f"{emoji} {max_name}",
                       bg=BG3, fg=T1, font=self.fx, padx=6, pady=1)
        lbl.pack(side=tk.LEFT, padx=2)

        # 点击×移除
        x_btn = tk.Label(self._attach_row, text=" ×", bg=BG3, fg=T3, font=self.fx,
                         cursor="hand2")
        x_btn.pack(side=tk.LEFT)
        idx = len(self._pending_files) - 1

        def remove(idx=idx, lbl=lbl, x_btn=x_btn):
            if 0 <= idx < len(self._pending_files):
                self._pending_files.pop(idx)
            lbl.destroy()
            x_btn.destroy()
            if not self._pending_files:
                self._attach_row.pack_forget()

        x_btn.bind("<Button-1>", lambda e: remove())
        self._file_labels.append((lbl, x_btn))

    def _process_attachments_for_message(self) -> str:
        """
        将待发送的附件处理为 prompt 文本。
        - 图片：添加路径说明（实际图片在 _send 中 base64 编码）
        - 文本文件：读取内容并附加
        """
        parts = []
        for f in self._pending_files:
            path = f["path"]
            ftype = f["type"]
            name = os.path.basename(path)
            if ftype == "image":
                parts.append(f"[图片: {name}]")
            else:
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    max_len = 8000
                    if len(content) > max_len:
                        content = content[:max_len] + f"\n…(文件过长，已截断，原{len(content)}字符)"
                    parts.append(f"[文件: {name}]\n```\n{content}\n```")
                except:
                    parts.append(f"[文件: {name} (无法读取)]")
        return "\n\n".join(parts)

    def _clear_attachments(self):
        """清空待发送附件"""
        self._pending_files.clear()
        self._attach_row.pack_forget()
        for lbl, x_btn in self._file_labels:
            lbl.destroy()
            x_btn.destroy()
        self._file_labels.clear()

    def _focus_inp(self):
        self.inp.focus_force()
        self.inp.focus_set()

    # ================== Gateway ==================

    def _gw_thread(self):
        def loop():
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3)
                    ok = s.connect_ex(("127.0.0.1", 18789)) == 0
                    s.close()
                    if ok and not self._gw_ok:
                        self._gw_ok = True
                        self.mq.put(("gw_ok",))
                    elif not ok:
                        self._gw_ok = False
                        self.mq.put(("gw_err","无连接"))
                except:
                    self.mq.put(("gw_err","检测失败"))
                time.sleep(10)
        threading.Thread(target=loop, daemon=True).start()
        self.root.after(500, self._poll)

    # ================== 会话管理 ==================

    def _load(self):
        self._refresh()
        for m in self.db.msgs(self.sid):
            if m["role"]=="user": self._user(m["content"])
            else: self._agent(m["content"],0)

    def _to_main(self):
        if self.sid == MAIN_ID: return
        self.sid = MAIN_ID
        self._redraw()
        self._refresh()

    def _new_hist(self):
        """新建会话 - 弹出命名对话框"""
        d = tk.Toplevel(self.root)
        d.title("新建会话")
        d.geometry("320x120")
        d.configure(bg=BG4)
        d.resizable(False, False)
        d.transient(self.root)
        d.grab_set()
        # 居中
        d.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()-320)//2
        y = self.root.winfo_y() + (self.root.winfo_height()-120)//2
        d.geometry(f"+{x}+{y}")

        tk.Label(d, text="会话名称", fg=T1, bg=BG4, font=self.fs).pack(pady=(12,4))
        e = tk.Entry(d, font=self.fn, bg=BG3, fg=T1, relief=tk.FLAT, bd=4,
                    insertbackground=AL, insertwidth=2)
        e.insert(0, "新会话")
        e.pack(fill=tk.X, padx=24, pady=(0,4))
        e.select_range(0, tk.END)
        e.focus_set()

        btns = tk.Frame(d, bg=BG4)
        btns.pack(fill=tk.X, padx=24, pady=(4,10))

        def ok():
            title = e.get().strip() or "新会话"
            self.sid = self.db.new_hist(title)
            self._redraw()
            self._refresh()
            d.destroy()

        tk.Button(btns, text="取消", bg=BG3, fg=T2, font=self.fs, borderwidth=0,
                 padx=14, pady=4, cursor="hand2", command=d.destroy,
                 activebackground=BG8, activeforeground=T1).pack(side=tk.RIGHT, padx=(8,0))
        tk.Button(btns, text="创建", bg=AC, fg="white", font=self.fs, borderwidth=0,
                 padx=14, pady=4, cursor="hand2", command=ok,
                 activebackground=AH, activeforeground="white").pack(side=tk.RIGHT)

        e.bind("<Return>", lambda ev: ok())
        d.bind("<Escape>", lambda ev: d.destroy())

    def _switch(self, sid):
        if sid == self.sid: return
        self.sid = sid
        self._redraw()
        self._refresh()

    def _del(self, sid):
        s = self.db.list()
        t = next((x for x in s if x["id"]==sid), None)
        if not t: return
        if t["main"]:
            messagebox.showinfo("提示","主对话不能删除")
            return
        if messagebox.askyesno("删除", f"永久删除「{t['title']}」？"):
            self.db.delete(sid)
            if sid == self.sid:
                self.sid = MAIN_ID
                self._redraw()
            self._refresh()

    def _rn(self, sid):
        s = self.db.list()
        t = next((x for x in s if x["id"]==sid), None)
        if not t or t["main"]: return

        d = tk.Toplevel(self.root)
        d.title("重命名"); d.geometry("280x100"); d.configure(bg=BG4)
        d.resizable(False,False); d.transient(self.root); d.grab_set()
        d.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()-280)//2
        y = self.root.winfo_y() + (self.root.winfo_height()-100)//2
        d.geometry(f"+{x}+{y}")

        tk.Label(d, text="新名称", fg=T1, bg=BG4, font=self.fs).pack(pady=(10,2))
        e = tk.Entry(d, font=self.fn, bg=BG3, fg=T1, relief=tk.FLAT, bd=4,
                    insertbackground=AL)
        e.insert(0, t["title"]); e.pack(fill=tk.X, padx=20, pady=(0,8))
        e.select_range(0, tk.END); e.focus_set()

        def doit():
            n = e.get().strip()
            if n: self.db.rename(sid,n); self._refresh()
            d.destroy()
        e.bind("<Return>", lambda ev: doit())
        d.bind("<Escape>", lambda ev: d.destroy())

    def _redraw(self):
        ca=self.ca; ca.configure(state=tk.NORMAL); ca.delete("1.0",tk.END)
        self.imgs.clear(); ca.configure(state=tk.DISABLED)
        for m in self.db.msgs(self.sid):
            if m["role"]=="user": self._user(m["content"])
            else: self._agent(m["content"],0)

    def _refresh(self):
        for w in self._hist: w.destroy()
        self._hist.clear()

        if self.sid == MAIN_ID:
            self.mb.configure(bg=BG7, fg=AL)
        else:
            self.mb.configure(bg=BG2, fg=T2)

        ss = [x for x in self.db.list() if not x["main"]]
        if not ss:
            e = tk.Label(self.hc, text="暂无历史会话", fg=T3, bg=BG2, font=self.fx, justify="center")
            e.pack(fill=tk.X, pady=20); self._hist.append(e)
            return

        for s in ss:
            act = (s["id"]==self.sid)
            bg = BG7 if act else BG2
            fg = AL if act else T2

            r = tk.Frame(self.hc, bg=bg, cursor="hand2")
            r.pack(fill=tk.X, pady=1); self._hist.append(r)

            lb = tk.Label(r, text=s["title"][:18], fg=fg, bg=bg, font=self.fx, anchor="w", padx=8, pady=6)
            lb.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def ent(e,r=r,a=act):
                if not a: r.configure(bg=BG8)
            def lve(e,r=r,a=act):
                if not a: r.configure(bg=BG2)
            r.bind("<Enter>",ent); r.bind("<Leave>",lve)

            sid = s["id"]
            for w in [r,lb]:
                w.bind("<Button-1>", lambda e,si=sid: self._switch(si))
                w.bind("<Button-3>", lambda e,si=sid: self._ctxmenu(e,si))

    def _ctxmenu(self, ev, sid):
        m = tk.Menu(self.root, tearoff=0, bg=BG4, fg=T1, font=self.fx,
                   activebackground=BG8, activeforeground=AL)
        m.add_command(label="重命名", command=lambda: self._rn(sid))
        m.add_command(label="删除", command=lambda: self._del(sid))
        m.tk_popup(ev.x_root, ev.y_root)

    # ================== 斜杠命令 ==================

    def _handle_command(self, msg: str) -> bool:
        """
        处理本地斜杠命令，返回 True 表示已处理（不发给 AI）。
        支持：
          /model <name>     切换模型
          /apikey <key>     设置 API Key
          /api <url>        设置 API 地址
          /config           查看当前配置
          /settings         打开设置窗口
        """
        config_path = os.path.join(BLUE_DIR, "config.json")
        msg = msg.strip()

        # /model <name>
        if msg.lower().startswith("/model"):
            parts = msg.split(None, 1)
            if len(parts) < 2:
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    ds = cfg.get("deepseek", {})
                    ol = cfg.get("ollama", {})
                    self._sys(f"🧠 DeepSeek 模型: {ds.get('model', '?')}")
                    self._sys(f"👁 Ollama 模型: {ol.get('model', '?')}")
                except:
                    self._sys("⚠ 无法读取配置")
                self._focus_inp()
                return True
            new_model = parts[1]
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                ds = cfg.get("deepseek", {})
                # 同步到 config.json + openclaw.json
                self._sync_api_config(ds.get("api_key", ""), ds.get("base_url", ""), new_model)
                self.model_label.configure(text=new_model)
                self._sys(f"✅ 模型已切换为: {new_model}")
            except Exception as e:
                self._sys(f"❌ 切换失败: {e}")
            self._focus_inp()
            return True

        # /apikey <key>
        if msg.lower().startswith("/apikey"):
            parts = msg.split(None, 1)
            if len(parts) < 2:
                self._sys("⚠ 用法: /apikey <你的API密钥>")
                self._focus_inp()
                return True
            new_key = parts[1]
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                ds = cfg.get("deepseek", {})
                self._sync_api_config(new_key, ds.get("base_url", ""), ds.get("model", ""))
                masked = new_key[:8] + "***" if len(new_key) > 8 else "***"
                self._sys(f"✅ API Key 已同步到全部配置: {masked}")
            except Exception as e:
                self._sys(f"❌ 设置失败: {e}")
            self._focus_inp()
            return True

        # /api <url>
        if msg.lower().startswith("/api"):
            parts = msg.split(None, 1)
            if len(parts) < 2:
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    self._sys(f"🔗 DeepSeek API: {cfg.get('deepseek', {}).get('base_url', '?')}")
                    self._sys(f"🔗 Ollama: {cfg.get('ollama', {}).get('base_url', '?')}")
                except:
                    self._sys("⚠ 无法读取配置")
                self._focus_inp()
                return True
            new_url = parts[1]
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                ds = cfg.get("deepseek", {})
                self._sync_api_config(ds.get("api_key", ""), new_url, ds.get("model", ""))
                self._sys(f"✅ API 地址已同步到全部配置: {new_url}")
            except Exception as e:
                self._sys(f"❌ 设置失败: {e}")
            self._focus_inp()
            return True

        # /config — 查看完整配置（隐藏 key）
        if msg.lower() == "/config":
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                ds = cfg.get("deepseek", {})
                ol = cfg.get("ollama", {})
                ex = cfg.get("execution", {})
                key = ds.get("api_key", "")
                masked = key[:8] + "***" + key[-4:] if len(key) > 12 else "***"
                self._sys(f"📋 当前配置:")
                self._sys(f"  DeepSeek API: {ds.get('base_url', '?')}")
                self._sys(f"  DeepSeek Key: {masked}")
                self._sys(f"  DeepSeek 模型: {ds.get('model', '?')}")
                self._sys(f"  Ollama: {ol.get('base_url', '?')} / {ol.get('model', '?')}")
                self._sys(f"  步延迟: {ex.get('step_delay_ms', '?')}ms | 重试: {ex.get('max_retries', '?')}")
            except:
                self._sys("⚠ 无法读取配置")
            self._focus_inp()
            return True

        # /settings — 打开设置窗口
        if msg.lower() == "/settings":
            self._open_settings()
            self._focus_inp()
            return True

        return False

    # ================== 发送消息 ==================

    def _send(self):
        msg = self.inp.get("1.0","end-1c").strip()

        # 有附件但没文字 → 自动填充默认提示
        has_files = bool(self._pending_files)
        if not msg and not has_files:
            self._focus_inp()
            return
        if not msg and has_files:
            img_count = sum(1 for f in self._pending_files if f["type"] == "image")
            file_count = len(self._pending_files) - img_count
            parts = []
            if img_count: parts.append(f"{img_count}张图片")
            if file_count: parts.append(f"{file_count}个文件")
            msg = f"请分析{'和'.join(parts)}的内容"

        if self.busy:
            self._focus_inp()
            return

        # 斜杠命令（无附件时）
        if not has_files and msg.startswith("/"):
            self.inp.delete("1.0","end")
            if self._handle_command(msg):
                return

        # 检测"开启00蓝色模式"密令
        if msg.strip() == "开启00蓝色模式":
            self.inp.delete("1.0","end")
            if not THEME_OK:
                self._sys("⚠ 主题模块未加载，无法切换")
                self._focus_inp()
                return
            if self.mode == "red":
                self._toggle_mode()
            else:
                self._sys("🔵 已经是蓝色模式（跳跳）了呀！")
            self._focus_inp()
            return

        # 拼接附件内容
        attachment_text = self._process_attachments_for_message() if has_files else ""
        full_msg = msg
        if attachment_text:
            full_msg = msg + "\n\n" + attachment_text

        # 快照待发送附件（发送后清理）
        pending_files = self._pending_files.copy()

        self.busy = True
        self.inp.delete("1.0","end")
        self._clear_attachments()
        self.btn_c.itemconfig(self._bc, fill=T3)
        self.btn_c.itemconfig(self._ba, text="⋯")
        self._status(YW,"思考中...")

        # 显示用户消息（含附件标签）
        display_msg = msg
        if pending_files:
            names = [os.path.basename(f["path"]) for f in pending_files]
            display_msg = "📎 " + ", ".join(names[:3]) + ("…" if len(names) > 3 else "") + "\n" + msg
        self.db.add(self.sid, "user", display_msg)
        self._user(display_msg)
        self._autoname()

        threading.Thread(target=self._call, args=(full_msg, pending_files), daemon=True).start()

    def _shot_and_see(self):
        """截图分析：蓝模式下走知新管道，红模式下简单描述"""
        if self.busy:
            return

        self.busy = True
        self.btn_v.itemconfig(self._bv, fill=T3)

        if self.mode == "blue" and THEME_OK:
            # 蓝模式：用知新管道执行任务
            self._status(YW, "🐬 跳跳正在分析任务...")
            threading.Thread(target=self._blue_task, daemon=True).start()
        else:
            # 红模式：简单视觉描述
            self._status(YW, "📷 正在截图分析...")
            threading.Thread(target=self._do_vision, daemon=True).start()

    def _blue_task(self):
        """蓝模式📷按钮：快速扫描屏幕，识别可交互元素"""
        try:
            import zhixin
            config = zhixin._load_config()
        except Exception as e:
            self.mq.put(("err", f"知新模块加载失败: {e}"))
            return

        try:
            self.root.after(0, lambda: self._status(YW, "📷 扫描屏幕中..."))

            # 截图
            import executor
            img_path = executor.screenshot()
            if not img_path:
                self.mq.put(("err", "截图失败"))
                return

            # Ollama 视觉扫描
            self.root.after(0, lambda: self._status(YW, "🔍 识别屏幕元素..."))
            prompt = (
                "用中文列出当前屏幕上所有可见的窗口、图标、按钮和可交互元素。"
                "格式：\n- 窗口：列出所有打开的窗口标题\n- 任务栏：可见的图标\n- 桌面：可见的快捷方式和控件\n"
                "简洁描述即可，不需要坐标。"
            )
            desc = zhixin._call_ollama_vision(img_path, prompt, config)

            if not desc:
                self.mq.put(("err", "视觉分析返回为空"))
                return

            # 显示结果
            self.db.add(self.sid, "user", "📷 看看屏幕")
            self._user("📷 看看屏幕")
            self.db.add(self.sid, "agent", f"🔍 屏幕扫描结果：\n\n{desc}")
            self.mq.put(("ok", desc, 0))
            self._autoname()

        except Exception as e:
            self.mq.put(("err", f"屏幕扫描失败: {e}"))

    def _do_vision(self):
        try:
            import urllib.request

            # 1. 截图
            cap_script = os.path.join(WORK, "skills", "screen-insight", "scripts", "capture.ps1")
            if not os.path.exists(cap_script):
                self.mq.put(("err", "截图脚本缺失，请检查 skills/ 目录"))
                return
            r = subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", cap_script, "-Mode", "screen"],
                capture_output=True, encoding="utf-8", errors="replace", timeout=30,
                cwd=WORK, creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = (r.stdout or "").split("\n")
            img_path = ""
            for ln in reversed(lines):
                ln = ln.strip()
                if ln.endswith(".png") and os.path.exists(ln):
                    img_path = ln
                    break
            if not img_path:
                self.mq.put(("err", "截图失败: 未生成图片"))
                return

            # 2. 读取截图并 base64
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("ascii")

            # 3. 调用 Ollama 视觉 API
            body = json.dumps({
                "model": "minicpm-v:8b",
                "prompt": "用中文简要描述这个屏幕上有什么。列出可见的窗口、大致内容。",
                "images": [img_b64],
                "stream": False,
                "options": {"num_gpu": 0}
            })

            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=body.encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            api_resp = urllib.request.urlopen(req, timeout=180)
            result = json.loads(api_resp.read().decode("utf-8"))
            desc = result.get("response", "").strip()

            if not desc:
                self.mq.put(("err", "视觉分析返回为空"))
                return

            # 4. 显示结果
            self.db.add(self.sid, "user", "📷 看看屏幕")
            self._user("📷 看看屏幕")
            self.db.add(self.sid, "agent", desc)
            self.mq.put(("ok", desc, 0))
            self._autoname()

        except Exception as e:
            self.mq.put(("err", f"视觉分析失败: {e}"))

    def _call(self, msg, pending_files=None):
        # ===== 蓝模式：走知新管道 =====
        if self.mode == "blue" and THEME_OK:
            self._blue_call(msg, pending_files)
            return

        # ===== 红模式：走 OpenClaw 纯对话 =====
        try:
            t0 = time.time()
            ctxs = self.db.ctx(self.sid, 8)

            ctxt = ""
            if len(ctxs) > 1:
                ctxt = "【对话历史】\n"
                for cm in ctxs[:-1]:
                    nm = "用户" if cm["role"]=="user" else "老六"
                    ctxt += f"{nm}: {cm['content'][:150]}\n"
                ctxt += "---\n【当前】"

            # 编码图片附件为 base64
            full = ctxt + msg
            if pending_files:
                for f in pending_files:
                    if f["type"] == "image":
                        try:
                            with open(f["path"], "rb") as img_f:
                                img_b64 = base64.b64encode(img_f.read()).decode("ascii")
                            full += f"\n\n[图片base64: data:image/png;base64,{img_b64}]"
                        except:
                            pass

            # 写入临时文件
            msg_file = os.path.join(DATA_DIR, "_msg.txt")
            with open(msg_file, "w", encoding="utf-8") as f:
                f.write(full)

            # 构建环境变量
            env = os.environ.copy()
            env["OPENCLAW_HOME"] = WORK
            env["NODE_HOME"] = NODE
            env["PATH"] = NODE + ";" + os.path.join(WORK, r"node_modules\.bin") + ";" + env.get("PATH", "")

            p = subprocess.Popen(
                [OPENCLAW, "agent", "--message-file", msg_file,
                 "--session-id", "s-"+self.sid, "--timeout","120", "--thinking","off"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="utf-8", errors="replace",
                cwd=WORK, env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            try:
                out, err = p.communicate(timeout=130)
                el = time.time() - t0
                out = out or ""
                err = err or ""
                resp = out.strip()
                if err.strip():
                    with open(os.path.join(DATA_DIR, "_debug.log"), "a", encoding="utf-8") as df:
                        df.write(f"[{datetime.now()}] STDERR: {err[:500]}\n")
                if not resp:
                    with open(os.path.join(DATA_DIR, "_debug.log"), "a", encoding="utf-8") as df:
                        df.write(f"[{datetime.now()}] EMPTY RESPONSE | stdout={out[:200]!r} | err={err[:200]!r} | rc={p.returncode}\n")
                    resp = "（无响应）"
                if err.strip():
                    skip = ["config warning","embedded fallback","gateway closed","plugins.allow","plugin not installed"]
                    if not any(x in err.lower() for x in skip):
                        resp += f"\n\n[诊断] {err[:200]}"
                self.db.add(self.sid, "agent", resp)
                self.mq.put(("ok", resp, el))
            except subprocess.TimeoutExpired:
                p.kill(); self.mq.put(("err","超时（2分钟）"))
        except Exception as e:
            tb = traceback.format_exc()
            with open(os.path.join(DATA_DIR, "_debug.log"), "a", encoding="utf-8") as df:
                df.write(f"[{datetime.now()}] EXCEPTION: {e}\n{tb}\n")
            self.mq.put(("err", f"失败: {e}\n{tb[-200:]}"))

    def _blue_call(self, msg, pending_files=None):
        """蓝模式核心：知新管道 → Claude Code"""
        import zhixin
        t0 = time.time()

        try:
            config = zhixin._load_config()
        except Exception as e:
            self.mq.put(("err", f"加载配置失败: {e}"))
            return

        self.root.after(0, lambda: self._status(YW, "🧠 理解任务意图..."))

        def progress_cb(status, idx, total):
            self.root.after(0, lambda: self._status(YW, status))

        def run_pipeline():
            try:
                prompt = msg
                img_paths = None
                if pending_files:
                    img_paths = [f["path"] for f in pending_files if f["type"] == "image"]
                    file_paths = [f["path"] for f in pending_files if f["type"] == "file"]
                    # 文本文件：提醒 Claude 去读取
                    for fp in file_paths:
                        prompt += f"\n[用户提供了文件: {fp}]"

                report = zhixin.run(prompt, progress_cb=progress_cb, config=config, image_paths=img_paths)
                el = time.time() - t0

                final = f"老大，我已完成任务 ✅\n\n📋 执行报告：\n{report}"
                self.db.add(self.sid, "agent", final)
                self.mq.put(("ok", final, el))
            except Exception as e:
                self.mq.put(("err", f"知新管道异常: {e}"))

        threading.Thread(target=run_pipeline, daemon=True).start()

    def _autoname(self):
        ss = self.db.list()
        t = next((x for x in ss if x["id"]==self.sid), None)
        if t and t["main"]: return
        ms = self.db.msgs(self.sid)
        um = [m for m in ms if m["role"]=="user"]
        if len(um)==1:
            title = um[0]["content"][:18].replace("\n"," ")
            self.db.rename(self.sid, title)
            self._refresh()

    # ================== 消息轮询 ==================

    def _poll(self):
        try:
            while True:
                it = self.mq.get_nowait()
                t = it[0]

                if t == "gw_ok":
                    self.sl.configure(text="已连接")
                    self.sd.itemconfig(self._si, fill=GR)
                elif t == "gw_err":
                    self.sl.configure(text=it[1])
                    self.sd.itemconfig(self._si, fill=RD)
                elif t == "ok":
                    _,resp,el = it
                    self._agent(resp, el)
                    self.busy = False
                    self.btn_c.itemconfig(self._bc, fill=AC)
                    self.btn_c.itemconfig(self._ba, text="↑")
                    self.btn_v.itemconfig(self._bv, fill="#5a3040")
                    self._status(GR,"就绪")
                    self._refresh()
                    self._focus_inp()
                elif t == "err":
                    self._err(f"⚠ {it[1]}")
                    self.busy = False
                    self.btn_c.itemconfig(self._bc, fill=AC)
                    self.btn_c.itemconfig(self._ba, text="↑")
                    self.btn_v.itemconfig(self._bv, fill="#5a3040")
                    self._status(RD,"出错")
                    self._focus_inp()
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    # ================== 渲染 ==================

    def _user(self, txt):
        ca=self.ca; ca.configure(state=tk.NORMAL)
        ca.insert(tk.END,"\n"); ca.insert(tk.END,"🧑 你\n","ul")
        ca.insert(tk.END, txt+"\n","ub")
        ca.configure(state=tk.DISABLED); ca.see(tk.END)

    def _agent(self, txt, el):
        ca=self.ca; ca.configure(state=tk.NORMAL); ca.insert(tk.END,"\n")
        es = f" · {el:.1f}s" if el>2 else ""
        meta = MODE_META.get(self.mode, {})
        em = meta.get("emoji", "🦞")
        name = meta.get("name", "老六")
        ca.insert(tk.END, f"{em} {name}{es}\n","al")

        imgs = self._findimgs(txt)
        if imgs:
            parts = [l for l in txt.split("\n") if not any(l.strip()==p or l.strip().startswith(p) for p in imgs)]
            cl = "\n".join(parts).strip()
            if cl: self._md(cl,"ab")
            for p in imgs:
                if os.path.exists(p): self._img(p)
        else:
            self._md(txt,"ab")
        ca.configure(state=tk.DISABLED); ca.see(tk.END)

    def _sys(self, txt):
        ca=self.ca; ca.configure(state=tk.NORMAL); ca.insert(tk.END,"\n")
        ca.insert(tk.END, f"  {txt}\n","sy"); ca.configure(state=tk.DISABLED); ca.see(tk.END)

    def _err(self, txt):
        ca=self.ca; ca.configure(state=tk.NORMAL); ca.insert(tk.END,"\n")
        ca.insert(tk.END, f"  {txt}\n","er"); ca.configure(state=tk.DISABLED); ca.see(tk.END)

    def _img(self, pth):
        ca=self.ca
        if not PIL_OK:
            ca.insert(tk.END, f"[图片] {pth}\n","ip"); return
        try:
            im = Image.open(pth)
            mw = max(ca.winfo_width()*0.55, 260)
            if im.width>mw:
                r = mw/im.width; im = im.resize((int(mw),int(im.height*r)), Image.LANCZOS)
            ph = ImageTk.PhotoImage(im); self.imgs.append(ph)
            ca.insert(tk.END,"\n"); ca.image_create(tk.END, image=ph)
            ca.insert(tk.END,"\n"); ca.insert(tk.END,f"  📁 {os.path.basename(pth)}\n","ip")
        except Exception as e:
            ca.insert(tk.END, f"[加载失败] {e}\n","er")

    def _md(self, txt, tag):
        ca=self.ca; ic=False; cl=[]
        for ln in txt.split("\n"):
            if ln.strip().startswith("```"):
                if ic:
                    if cl: ca.insert(tk.END, "\n".join(cl)+"\n","cd")
                    cl=[]; ic=False
                else: ic=True
                continue
            if ic: cl.append(ln); continue
            ps = re.split(r"(\*\*[^*]+\*\*)", ln)
            for p in ps:
                if p.startswith("**") and p.endswith("**"):
                    ca.insert(tk.END, p[2:-2], ("bo",tag))
                elif re.match(r"^https?://", p):
                    ca.insert(tk.END, p, "lk")
                else:
                    ca.insert(tk.END, p, tag)
            ca.insert(tk.END,"\n",tag)
        if cl: ca.insert(tk.END, "\n".join(cl)+"\n","cd")

    def _findimgs(self, txt):
        ps=[]
        for m in re.findall(r'([A-Za-z]:[\\/][^\s\n]*?\.(?:png|jpg|jpeg|gif|bmp|webp))', txt, re.IGNORECASE):
            p=m.replace("/","\\")
            if os.path.exists(p) and p not in ps: ps.append(p)
        return ps

    # ================== 辅助 ==================

    def _status(self, color, text):
        self.sd.itemconfig(self._si, fill=color)
        self.sl.configure(text=text)

    def _nl(self):
        self.inp.insert(tk.INSERT,"\n")
        return "break"

    def _cls(self):
        if self.busy: return
        self._redraw()
        self._sys("显示已刷新")

    def _start(self):
        meta = MODE_META.get("red", {})
        em = meta.get("emoji", "🦞")
        name = meta.get("name", "老六")
        self._sys(f"{em} {name} Chat 已就绪\nEnter 发送  ·  Shift+Enter 换行\n⭐ 主对话每4天清理  ·  💬 历史会话永久保留")

    # ================== 模式切换 ==================

    def _toggle_mode(self):
        """切换红色/蓝色模式"""
        if not THEME_OK:
            messagebox.showinfo("提示", "主题模块未加载，无法切换模式")
            return

        if self.busy:
            return

        if self.mode == "red":
            self.mode = "blue"
            self.theme = BLUE
            self._update_globals(BLUE)
        else:
            self.mode = "red"
            self.theme = RED
            self._update_globals(RED)

        self._apply_theme()

        meta = MODE_META.get(self.mode, {})
        em = meta.get("emoji", "?")
        name = meta.get("name", "?")
        desc = meta.get("desc", "")

        self.root.title(f"{name} Chat")
        self._sys(f"已切换至 {em} {name} {desc}")

        # 更新模式按钮
        if self.mode == "red":
            self.mode_btn.configure(text="🔵 切换跳跳", bg=AC, activebackground=AH)
        else:
            self.mode_btn.configure(text="🔴 切换老六", bg=AC, activebackground=AH)

        # 蓝模式：启动温故
        if self.mode == "blue" and self.wengu:
            try:
                self.wengu.start()
            except:
                pass

    def _update_globals(self, theme):
        """更新模块级颜色变量"""
        global BG0, BG1, BG2, BG3, BG4, BG5, BG6, BG7, BG8
        global CB, CF, AC, AH, AL, T1, T2, T3, GR, YW, RD
        global INP_BG, INP_FG, INP_BDR, BAR_BG, BAR_HINT
        BG0 = theme.get("BG0", BG0); BG1 = theme.get("BG1", BG1)
        BG2 = theme.get("BG2", BG2); BG3 = theme.get("BG3", BG3)
        BG4 = theme.get("BG4", BG4); BG5 = theme.get("BG5", BG5)
        BG6 = theme.get("BG6", BG6); BG7 = theme.get("BG7", BG7)
        BG8 = theme.get("BG8", BG8); CB = theme.get("CB", CB)
        CF = theme.get("CF", CF); AC = theme.get("AC", AC)
        AH = theme.get("AH", AH); AL = theme.get("AL", AL)
        T1 = theme.get("T1", T1); T2 = theme.get("T2", T2)
        T3 = theme.get("T3", T3); GR = theme.get("GR", GR)
        YW = theme.get("YW", YW); RD = theme.get("RD", RD)
        INP_BG = theme.get("INP_BG", INP_BG); INP_FG = theme.get("INP_FG", INP_FG)
        INP_BDR = theme.get("INP_BDR", INP_BDR); BAR_BG = theme.get("BAR_BG", BAR_BG)
        BAR_HINT = theme.get("BAR_HINT", BAR_HINT)

    def _apply_theme(self):
        """将主题颜色应用到所有可见 widget"""
        t = self.theme

        # Root
        self.root.configure(bg=t.get("BG0", BG0))

        # Sidebar
        self.sb.configure(bg=t.get("BG2", BG2))

        # Chat area
        self.ca.configure(bg=t.get("BG1", BG1), fg=t.get("T1", T1), insertbackground=t.get("T1", T1))

        # Input
        try:
            self.inp.configure(bg=t.get("INP_BG", INP_BG), fg=t.get("INP_FG", INP_FG),
                              insertbackground=t.get("AC", AC))
            self._inp_canvas.configure(bg=t.get("BAR_BG", BAR_BG))
        except:
            pass

        # Buttons
        try:
            self.btn_c.itemconfig(self._bc, fill=t.get("AC", AC))
            self.btn_v.itemconfig(self._bv, fill="#5a3040" if self.mode == "red" else "#30405a")
            self.mode_btn.configure(bg=t.get("AC", AC), activebackground=t.get("AH", AH))
        except:
            pass

        # Status
        try:
            self.sd.configure(bg=t.get("BG2", BG2))
        except:
            pass

        # Update tags
        self.ca.tag_configure("ub", background=t.get("BG5", BG5))
        self.ca.tag_configure("ab", background=t.get("BG6", BG6))
        self.ca.tag_configure("al", foreground=t.get("AC", AC))
        self.ca.tag_configure("ul", foreground=t.get("AL", AL))

    # ================== 内联设置面板 ==================

    def _sync_api_config(self, api_key: str, api_url: str = None, model: str = None):
        """
        同步 API 配置到 config.json 和 openclaw.json。
        这是整个程序唯一写入 API Key 的地方 — 一个输入，两个文件同步。
        """
        config_path = os.path.join(BLUE_DIR, "config.json")
        openclaw_path = os.path.join(WORK, ".openclaw", "openclaw.json")

        # 1. 写 blue-mode/config.json
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            cfg = {}
        cfg.setdefault("deepseek", {})["api_key"] = api_key
        if api_url:
            cfg.setdefault("deepseek", {})["base_url"] = api_url
        if model:
            cfg.setdefault("deepseek", {})["model"] = model
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

        # 2. 同步到 .openclaw/openclaw.json（红模式 OpenClaw 用）
        try:
            with open(openclaw_path, "r", encoding="utf-8") as f:
                oc = json.load(f)
            # 更新 deepseek provider 的 apiKey 和 baseUrl
            providers = oc.setdefault("models", {}).setdefault("providers", {})
            ds = providers.setdefault("deepseek", {})
            ds["apiKey"] = api_key
            if api_url:
                ds["baseUrl"] = api_url
            if model:
                # 更新模型列表中的 model id
                ds_models = ds.get("models", [])
                if ds_models:
                    ds_models[0]["id"] = model
                    ds_models[0]["name"] = model
                # 也更新 agents.defaults.model.primary
                oc.setdefault("agents", {}).setdefault("defaults", {}).setdefault("model", {})["primary"] = f"deepseek/{model}"
            with open(openclaw_path, "w", encoding="utf-8") as f:
                json.dump(oc, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # openclaw.json 不存在或损坏不算致命错误
            pass

    def _toggle_settings_panel(self):
        """展开/收起侧边栏设置面板"""
        if self._settings_expanded:
            self._settings_panel.pack_forget()
            self.settings_btn.configure(text="⚙ 设置 API")
            self._settings_expanded = False
        else:
            self._load_inline_settings()
            self._settings_panel.pack(fill=tk.X, padx=10, pady=(0, 6),
                                       before=self.model_label)
            self.settings_btn.configure(text="⚙ 收起设置")
            self._settings_expanded = True

    def _load_inline_settings(self):
        """从 config.json 加载当前设置到面板字段"""
        config_path = os.path.join(BLUE_DIR, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            ds = cfg.get("deepseek", {})
            self._api_url_entry.delete(0, tk.END)
            self._api_url_entry.insert(0, ds.get("base_url", "https://api.deepseek.com/v1"))
            self._api_key_entry.delete(0, tk.END)
            self._api_key_entry.insert(0, ds.get("api_key", ""))
            model = ds.get("model", "deepseek-v4-flash")
            self._model_var.set(model)
        except:
            pass

    def _toggle_key_visibility(self):
        """切换 API Key 的可见性"""
        if self._api_key_entry.cget("show") == "•":
            self._api_key_entry.configure(show="")
            self._show_key_btn.configure(text="🙈")
        else:
            self._api_key_entry.configure(show="•")
            self._show_key_btn.configure(text="👁")

    def _save_inline_settings(self):
        """保存内联设置（同时写 config.json + openclaw.json）"""
        api_url = self._api_url_entry.get().strip()
        api_key = self._api_key_entry.get().strip()
        model = self._model_var.get()

        if not api_url:
            self._sys("⚠ API 地址不能为空")
            return
        if not api_key:
            self._sys("⚠ API Key 不能为空")
            return

        try:
            self._sync_api_config(api_key, api_url, model)
            self.model_label.configure(text=model)
            masked = api_key[:8] + "***" if len(api_key) > 8 else "***"
            self._sys(f"✅ 已保存到全部配置 — 模型: {model} | Key: {masked}")
            self.root.after(600, self._toggle_settings_panel)
        except Exception as e:
            self._sys(f"❌ 保存失败: {e}")

    # ================== 设置窗口 ==================

    def _open_settings(self):
        """打开 API 配置窗口（完整版，含 Ollama 设置）"""
        d = tk.Toplevel(self.root)
        d.title("API 设置")
        d.geometry("420x340")
        d.configure(bg=BG4)
        d.resizable(False, False)
        d.transient(self.root)
        d.grab_set()
        d.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 420) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 340) // 2
        d.geometry(f"+{x}+{y}")

        # 加载配置
        config_path = os.path.join(BLUE_DIR, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            cfg = {"deepseek": {"base_url": "", "api_key": "", "model": ""},
                   "ollama": {"base_url": "", "model": ""}}

        tk.Label(d, text="⚙ API 配置", fg=T1, bg=BG4, font=self.ft).pack(pady=(12, 8))

        # DeepSeek 配置
        ds_frame = tk.LabelFrame(d, text="DeepSeek", fg=T2, bg=BG4, font=self.fs,
                                 padx=10, pady=8)
        ds_frame.pack(fill=tk.X, padx=20, pady=(0, 8))

        fields = [
            ("API URL", "deepseek", "base_url"),
            ("API Key", "deepseek", "api_key"),
            ("Model", "deepseek", "model"),
        ]
        entries = {}
        for label, section, key in fields:
            row = tk.Frame(ds_frame, bg=BG4)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label + ":", fg=T2, bg=BG4, font=self.fx, width=10, anchor="e").pack(side=tk.LEFT)
            e = tk.Entry(row, font=self.fs, bg=BG3, fg=T1, relief=tk.FLAT, bd=3, insertbackground=AL, width=30)
            val = cfg.get(section, {}).get(key, "")
            e.insert(0, str(val))
            e.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)
            entries[f"{section}.{key}"] = e

        # Ollama 配置
        ol_frame = tk.LabelFrame(d, text="Ollama", fg=T2, bg=BG4, font=self.fs,
                                 padx=10, pady=8)
        ol_frame.pack(fill=tk.X, padx=20, pady=(0, 8))

        for label, section, key in [("API URL", "ollama", "base_url"), ("Model", "ollama", "model")]:
            row = tk.Frame(ol_frame, bg=BG4)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label + ":", fg=T2, bg=BG4, font=self.fx, width=10, anchor="e").pack(side=tk.LEFT)
            e = tk.Entry(row, font=self.fs, bg=BG3, fg=T1, relief=tk.FLAT, bd=3, insertbackground=AL, width=30)
            val = cfg.get(section, {}).get(key, "")
            e.insert(0, str(val))
            e.pack(side=tk.LEFT, padx=(6, 0), fill=tk.X, expand=True)
            entries[f"{section}.{key}"] = e

        def save():
            for k, e in entries.items():
                section, key = k.split(".", 1)
                if section not in cfg:
                    cfg[section] = {}
                cfg[section][key] = e.get().strip()
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", "配置已保存")
                d.destroy()
            except Exception as ex:
                messagebox.showerror("失败", f"保存失败: {ex}")

        btns = tk.Frame(d, bg=BG4)
        btns.pack(fill=tk.X, padx=20, pady=(4, 10))
        tk.Button(btns, text="取消", bg=BG3, fg=T2, font=self.fs, borderwidth=0,
                 padx=14, pady=5, cursor="hand2", command=d.destroy,
                 activebackground=BG8, activeforeground=T1).pack(side=tk.RIGHT, padx=(8, 0))
        tk.Button(btns, text="保存", bg=AC, fg="white", font=self.fs, borderwidth=0,
                 padx=14, pady=5, cursor="hand2", command=save,
                 activebackground=AH, activeforeground="white").pack(side=tk.RIGHT)

        d.bind("<Escape>", lambda ev: d.destroy())


def main():
    root = tk.Tk()
    root.configure(bg=BG0)
    app = App(root)
    root.after(400, app._start)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

if __name__=="__main__":
    main()
