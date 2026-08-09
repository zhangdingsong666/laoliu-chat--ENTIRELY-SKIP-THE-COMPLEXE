"""
跳跳 操作执行器
封装 desktop-control PowerShell 脚本，提供 Python 接口
"""
import subprocess
import os
import time

# 路径：基于脚本位置，不再硬编码
_BLUE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(_BLUE_DIR)
SCRIPTS = os.path.join(WORK, "skills")
SCREENSHOTS_DIR = os.path.join(_BLUE_DIR, "screenshots")
DEBUG_LOG = os.path.join(_BLUE_DIR, "zhixin_debug.log")
CLICK_PS1 = os.path.join(SCRIPTS, "desktop-control", "scripts", "click.ps1")
TYPE_PS1 = os.path.join(SCRIPTS, "desktop-control", "scripts", "type.ps1")
WINDOW_PS1 = os.path.join(SCRIPTS, "desktop-control", "scripts", "window.ps1")
CAPTURE_PS1 = os.path.join(SCRIPTS, "screen-insight", "scripts", "capture.ps1")

PS_ARGS = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File"]
HIDDEN = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

# 检测 PIL 是否可用
try:
    from PIL import ImageGrab
    PIL_OK = True
except ImportError:
    PIL_OK = False


def _debug(msg: str):
    """写调试日志"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[executor {ts}] {msg}"
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def _run(args, timeout=15):
    """执行 PowerShell 命令，返回 (success, output)"""
    try:
        r = subprocess.run(
            args,
            capture_output=True,
            encoding="utf-8", errors="replace",
            timeout=timeout,
            cwd=WORK,
            creationflags=HIDDEN
        )
        out = (r.stdout or "").strip()
        if r.returncode != 0:
            err = (r.stderr or "").strip()
            return False, out + ("\n" + err if err else "")
        return True, out
    except subprocess.TimeoutExpired:
        return False, "操作超时"
    except Exception as e:
        return False, str(e)


# ===== 鼠标操作 =====

def move(x: int, y: int) -> bool:
    """移动鼠标到指定坐标"""
    ok, out = _run(PS_ARGS + [CLICK_PS1, "-Action", "move", "-X", str(x), "-Y", str(y)])
    return ok


def click(x: int = None, y: int = None) -> bool:
    """点击（先移动再点击）"""
    if x is not None and y is not None:
        if not move(x, y):
            return False
    ok, out = _run(PS_ARGS + [CLICK_PS1, "-Action", "click"])
    time.sleep(0.3)
    return ok


def double_click(x: int = None, y: int = None) -> bool:
    """双击"""
    if x is not None and y is not None:
        if not move(x, y):
            return False
    ok, out = _run(PS_ARGS + [CLICK_PS1, "-Action", "doubleclick"])
    time.sleep(0.3)
    return ok


def right_click(x: int = None, y: int = None) -> bool:
    """右键点击"""
    if x is not None and y is not None:
        if not move(x, y):
            return False
    ok, out = _run(PS_ARGS + [CLICK_PS1, "-Action", "rightclick"])
    time.sleep(0.3)
    return ok


def get_pos() -> tuple[int, int] | None:
    """获取当前鼠标位置"""
    ok, out = _run(PS_ARGS + [CLICK_PS1, "-Action", "getpos"])
    if ok:
        import re
        m = re.search(r'X=(\d+).*?Y=(\d+)', out)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def drag(x: int, y: int) -> bool:
    """拖拽到指定位置"""
    ok, out = _run(PS_ARGS + [CLICK_PS1, "-Action", "drag", "-X", str(x), "-Y", str(y)])
    time.sleep(0.5)
    return ok


# ===== 键盘操作 =====

def type_text(text: str) -> bool:
    """输入文本（发送到当前焦点窗口）"""
    ok, out = _run(PS_ARGS + [TYPE_PS1, "-Text", text])
    time.sleep(0.1 * len(text) + 1.0)  # 等待输入完成
    return ok


def press_keys(keys: str) -> bool:
    """发送组合键，如 '^c' (Ctrl+C), '%{TAB}' (Alt+Tab), '{ENTER}' (回车)"""
    ok, out = _run(PS_ARGS + [TYPE_PS1, "-Keys", keys])
    time.sleep(0.5)
    return ok


def press_enter() -> bool:
    return press_keys("{ENTER}")


def press_escape() -> bool:
    return press_keys("{ESC}")


def press_win() -> bool:
    return press_keys("^{ESC}")  # Win键


def copy() -> bool:
    return press_keys("^c")


def paste() -> bool:
    return press_keys("^v")


def press_win_r() -> bool:
    """Win+R 打开运行"""
    ok, out = _run(
        PS_ARGS + [TYPE_PS1, "-Keys", "^{ESC}"],
        timeout=5
    )
    if ok:
        time.sleep(0.5)
        ok2, _ = _run(PS_ARGS + [TYPE_PS1, "-Text", "r"], timeout=5)
        ok = ok and ok2
    return ok


# ===== 窗口操作 =====

def list_windows() -> str:
    """列出所有可见窗口"""
    ok, out = _run(PS_ARGS + [WINDOW_PS1, "-Action", "list"])
    return out


def find_window(title: str) -> str | None:
    """查找窗口，返回进程信息"""
    ok, out = _run(PS_ARGS + [WINDOW_PS1, "-Action", "find", "-Title", title])
    if ok and out and "No window found" not in out:
        return out
    return None


def focus_window(title: str) -> bool:
    """聚焦窗口"""
    ok, out = _run(PS_ARGS + [WINDOW_PS1, "-Action", "focus", "-Title", title])
    return ok


def minimize_window(title: str) -> bool:
    ok, out = _run(PS_ARGS + [WINDOW_PS1, "-Action", "minimize", "-Title", title])
    return ok


def maximize_window(title: str) -> bool:
    ok, out = _run(PS_ARGS + [WINDOW_PS1, "-Action", "maximize", "-Title", title])
    return ok


# ===== 截屏 =====

def screenshot(mode: str = "screen") -> str | None:
    """
    截屏，返回图片路径。
    优先使用 PowerShell 脚本，失败时回退到 PIL ImageGrab。
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")

    # ---- 方案 A: PowerShell 截图 ----
    ok, out = _run(PS_ARGS + [CAPTURE_PS1, "-Mode", mode, "-OutputDir", SCREENSHOTS_DIR], timeout=20)
    if ok:
        for line in reversed(out.split("\n")):
            line = line.strip()
            if line.lower().endswith(".png") and os.path.exists(line):
                _debug(f"PowerShell 截图成功: {line}")
                return line
        _debug(f"PowerShell 截图返回 ok 但未找到 png 文件，stdout: {out[:300]}")

    # ---- 方案 B: PIL ImageGrab 回退 ----
    if PIL_OK:
        _debug(f"PowerShell 截图失败，尝试 PIL 回退... (PS输出: {out[:200] if not ok else 'ok but no file'})")
        try:
            img_path = os.path.join(SCREENSHOTS_DIR, f"screenshot-pil-{ts}.png")
            # 尝试 all_screens（Pillow >= 9.1.0），失败则回退到单屏
            try:
                img = ImageGrab.grab(all_screens=True)
            except TypeError:
                _debug("PIL: all_screens 不支持，回退到单屏截图")
                img = ImageGrab.grab()
            img.save(img_path, "PNG")
            if os.path.exists(img_path):
                _debug(f"PIL 截图成功: {img_path} ({os.path.getsize(img_path)} bytes)")
                return img_path
        except Exception as e:
            _debug(f"PIL 截图也失败: {e}")
    else:
        _debug(f"PowerShell 截图失败且 PIL 不可用 (PS输出: {out[:300] if not ok else 'ok but no file'})")

    return None


def wait(seconds: float):
    """等待指定秒数"""
    time.sleep(seconds)
