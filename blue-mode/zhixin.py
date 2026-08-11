"""
知新 (Know New) — 跳跳核心管道
用户指令 → DeepSeek语义分解 → Ollama视觉定位 → DeepSeek匹配规划 → 执行

v2: 添加 OpenClaw 回退、调试日志、重试机制
"""
import json
import os
import time
import base64
import urllib.request
import urllib.error
import subprocess
import traceback

import executor

# 路径：基于脚本位置，不再硬编码
_BLUE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(_BLUE_DIR)  # blue-mode 的父目录即项目根
CONFIG_PATH = os.path.join(_BLUE_DIR, "config.json")
SCREENSHOTS_DIR = os.path.join(_BLUE_DIR, "screenshots")
DEBUG_LOG = os.path.join(_BLUE_DIR, "zhixin_debug.log")
OPENCLAW = os.path.join(WORK, r"node_modules\.bin\openclaw.cmd")
NODE = os.path.join(WORK, "nodejs")


def _debug(msg: str):
    """写调试日志"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def _load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # 环境变量覆盖配置文件（保护隐私：Key 可以不写文件，设环境变量即可）
    env_key = os.environ.get("DEEPSEEK_API_KEY", "") or os.environ.get("DEEPSEEK_KEY", "")
    env_url = os.environ.get("DEEPSEEK_API_URL", "") or os.environ.get("DEEPSEEK_BASE_URL", "")
    env_model = os.environ.get("DEEPSEEK_MODEL", "")
    if env_key:
        cfg.setdefault("deepseek", {})["api_key"] = env_key
    if env_url:
        cfg.setdefault("deepseek", {})["base_url"] = env_url
    if env_model:
        cfg.setdefault("deepseek", {})["model"] = env_model
    return cfg


# ===== OpenClaw 子进程回退 =====

def _call_deepseek_via_openclaw(prompt: str, config: dict = None, system: str = None, max_tokens: int = 2048) -> str:
    """
    通过 OpenClaw 子进程调用 DeepSeek（回退方案）
    当直接 API 调用失败时使用此路径
    """
    _debug(f"[OpenClaw回退] 尝试通过 openclaw agent 调用...")

    # 构建完整消息
    full_prompt = prompt
    if system:
        full_prompt = f"[系统指令]\n{system}\n\n[任务]\n{prompt}\n\n请直接输出结果，不要额外解释。"

    # 写入临时文件
    msg_file = os.path.join(SCREENSHOTS_DIR, "_openclaw_fallback.txt")
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    with open(msg_file, "w", encoding="utf-8") as f:
        f.write(full_prompt)

    env = os.environ.copy()
    env["NODE_HOME"] = NODE
    env["OPENCLAW_HOME"] = WORK
    env["PATH"] = NODE + ";" + os.path.join(WORK, r"node_modules\.bin") + ";" + env.get("PATH", "")

    try:
        p = subprocess.Popen(
            [OPENCLAW, "agent", "--message-file", msg_file,
             "--timeout", "60", "--thinking", "off",
             "--session-key", "agent:default:zhixin-fallback"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace",
            cwd=WORK, env=env,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        out, err = p.communicate(timeout=70)
        out = (out or "").strip()
        err = (err or "").strip()

        _debug(f"[OpenClaw回退] stdout({len(out)}): {out[:500]}")
        if err:
            # 过滤已知无害的警告
            harmless = ["config warning", "embedded fallback", "gateway closed",
                       "plugins.allow", "plugin not installed"]
            if not any(x in err.lower() for x in harmless):
                _debug(f"[OpenClaw回退] stderr: {err[:500]}")

        return out if out else ""

    except subprocess.TimeoutExpired:
        p.kill()
        _debug("[OpenClaw回退] 超时")
        return ""
    except Exception as e:
        _debug(f"[OpenClaw回退] 异常: {e}")
        return ""


# ===== DeepSeek API 调用 =====

def _call_deepseek(prompt: str, config: dict = None, system: str = None, max_tokens: int = 4096) -> str:
    """
    调用 DeepSeek API（直接 HTTP），失败时回退到 OpenClaw
    """
    if config is None:
        config = _load_config()
    ds = config["deepseek"]

    # ---- 方案 A: 直接 HTTP 调用 ----
    url = ds["base_url"].rstrip("/") + "/chat/completions"
    model = ds.get("model", "deepseek-v4-flash")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3
    }).encode("utf-8")

    for attempt in range(2):  # 最多重试2次
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ds['api_key']}"
                }
            )
            resp = urllib.request.urlopen(req, timeout=60)
            result = json.loads(resp.read().decode("utf-8"))
            msg = result["choices"][0]["message"]
            content = msg.get("content", "")
            finish_reason = result["choices"][0].get("finish_reason", "")
            reasoning_len = len(msg.get("reasoning_content", ""))
            _debug(f"[DeepSeek直接] 成功，content={len(content)}字符, reasoning={reasoning_len}字符, finish={finish_reason}")

            if not content and reasoning_len > 0 and finish_reason == "length":
                # 推理模型把所有 token 用于思考，无余量输出 → 加大 max_tokens 重试
                new_max = min(max_tokens * 2, 16384)
                _debug(f"[DeepSeek直接] 推理模型 token 不足 ({max_tokens}→{new_max})，重试...")
                body = json.dumps({
                    "model": model,
                    "messages": messages,
                    "max_tokens": new_max,
                    "temperature": 0.3
                }).encode("utf-8")
                max_tokens = new_max
                continue  # 回到 retry loop

            if not content:
                _debug("[DeepSeek直接] content 为空，当作失败处理")
                break
            return content

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")[:500]
            except:
                pass
            _debug(f"[DeepSeek直接] HTTP {e.code} (尝试 {attempt+1}/2): {err_body}")

            if e.code == 401:
                # 认证失败 — 不重试，直接回退
                _debug("[DeepSeek直接] API Key 无效，回退到 OpenClaw")
                break
            if e.code in (429, 500, 502, 503):
                # 可重试的错误
                if attempt < 1:
                    time.sleep(2 * (attempt + 1))
                    continue
            break  # 其他 HTTP 错误不回退

        except urllib.error.URLError as e:
            _debug(f"[DeepSeek直接] 网络错误 (尝试 {attempt+1}/2): {e}")
            if attempt < 1:
                time.sleep(2)
                continue
            break

        except Exception as e:
            _debug(f"[DeepSeek直接] 未知错误 (尝试 {attempt+1}/2): {e}")
            if attempt < 1:
                time.sleep(2)
                continue
            break

    # ---- 方案 B: OpenClaw 子进程回退 ----
    _debug("[DeepSeek] 直接调用失败，启用 OpenClaw 回退...")
    fallback_result = _call_deepseek_via_openclaw(prompt, config, system, max_tokens)
    if fallback_result:
        _debug(f"[DeepSeek回退] 成功，{len(fallback_result)} 字符")
        return fallback_result

    _debug("[DeepSeek回退] 也失败了，返回空字符串")
    return ""


# ===== Ollama 视觉调用 =====

def _call_ollama_vision(image_path: str, prompt: str, config: dict = None) -> str:
    """
    调用 Ollama 视觉模型，带重试和错误处理
    """
    if config is None:
        config = _load_config()
    ol = config["ollama"]

    if not os.path.exists(image_path):
        _debug(f"[Ollama视觉] 图片不存在: {image_path}")
        return ""

    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("ascii")
    except Exception as e:
        _debug(f"[Ollama视觉] 读取图片失败: {e}")
        return ""

    model = ol.get("model", "minicpm-v:8b")
    url = ol["base_url"].rstrip("/") + "/api/generate"

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"num_gpu": 0, "num_predict": 1024}
    }).encode("utf-8")

    for attempt in range(2):
        try:
            _debug(f"[Ollama视觉] 调用 {model} (尝试 {attempt+1}/2)...")
            t0 = time.time()
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=300)  # CPU推理需要更长时间
            result = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            content = result.get("response", "").strip()
            _debug(f"[Ollama视觉] 成功，{len(content)} 字符，耗时 {elapsed:.1f}s")
            return content

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")[:300]
            except:
                pass
            _debug(f"[Ollama视觉] HTTP {e.code} (尝试 {attempt+1}/2): {err_body}")
            if attempt < 1:
                time.sleep(3)
                continue

        except urllib.error.URLError as e:
            _debug(f"[Ollama视觉] 连接失败 (尝试 {attempt+1}/2): {e}")
            if attempt < 1:
                time.sleep(3)
                continue

        except Exception as e:
            _debug(f"[Ollama视觉] 未知错误 (尝试 {attempt+1}/2): {e}")
            if attempt < 1:
                time.sleep(3)
                continue

    _debug("[Ollama视觉] 所有尝试失败，返回空字符串")
    return ""


# ===== JSON 解析辅助 =====

def _extract_json(text: str):
    """
    从模型输出中提取 JSON，支持多种格式。
    处理 LLM 常见错误：尾部逗号、markdown 代码块、非标准包装。
    """
    if not text or not text.strip():
        return None

    import re

    original = text
    text = text.strip()

    # 预处理: 修复 LLM 常见的尾部逗号（如 [..., {"conf":0.9},]）
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # 策略1: 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 策略2: 去除 markdown 代码块
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # 策略3: 正则提取 JSON 对象
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    # 策略4: 正则提取 JSON 数组
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    _debug(f"[JSON提取] 所有策略失败，原文前300字符: {original[:300]}")
    return None


# ===== 管道步骤 =====

def understand_intent(user_cmd: str, config: dict = None) -> dict:
    """
    Step 1: 用 DeepSeek 将用户指令分解为操作步骤
    返回: {"goal": "...", "steps": [{"action":"click/type/wait/focus", "target":"..."}]}
    """
    if config is None:
        config = _load_config()

    system = (
        "你是一个桌面自动化规划专家。用户会给你一个操作指令，你需要将其分解为具体的桌面操作步骤。"
        "你可以使用的操作类型：\n"
        "- click: 点击某个按钮/图标/区域\n"
        "- double_click: 双击\n"
        "- type: 输入文字\n"
        "- press: 按组合键（如 Win+R, Ctrl+V, Enter, Esc）\n"
        "- focus: 聚焦某个窗口\n"
        "- wait: 等待\n\n"
        "重要规则：\n"
        "1. 不要猜测坐标 — 坐标由视觉系统提供\n"
        "2. 用自然语言描述目标（如'微信图标''搜索框''发送按钮'），不要用坐标\n"
        "3. 考虑合理的操作顺序和等待时间\n"
        "4. 包含验证步骤\n\n"
        "返回严格的JSON格式（不要包含markdown标记）：\n"
        '{"goal":"任务目标简述","steps":[{"action":"click","target":"目标描述","note":"补充说明"},...]}'
    )

    prompt = f"请为以下指令规划桌面操作步骤：\n\n{user_cmd}\n\n请返回JSON。"
    _debug(f"[语义理解] 输入: {user_cmd[:100]}")

    response = _call_deepseek(prompt, config, system, max_tokens=4096)
    _debug(f"[语义理解] 原始响应({len(response)}): {response[:500]}")

    if not response:
        _debug("[语义理解] DeepSeek 返回空响应")
        return {"goal": "理解失败（API无响应）", "steps": [], "raw": ""}

    result = _extract_json(response)
    if result and isinstance(result, dict):
        if "goal" in result and "steps" in result:
            _debug(f"[语义理解] 成功: goal={result.get('goal','?')}, steps={len(result.get('steps',[]))}")
            return result
        # 尝试适配不同的 JSON 结构
        if "steps" in result:
            result["goal"] = result.get("goal", user_cmd[:30])
            return result

    # 尝试从文本中提取步骤
    _debug("[语义理解] JSON解析失败，尝试从文本推断步骤...")
    # 直接返回原始响应，让后续步骤处理
    return {
        "goal": f"执行: {user_cmd[:30]}",
        "steps": [],
        "raw": response,
        "parse_error": True
    }


def scan_screen(config: dict = None) -> list:
    """
    Step 2: 截屏并用 Ollama 视觉模型定位UI元素
    返回: [{"name":"微信","center":[140,230],"bbox":[100,200,180,260],"conf":0.9}, ...]
    """
    if config is None:
        config = _load_config()

    # 截图（executor.screenshot 内部已有 PowerShell → PIL 双重回退）
    _debug("[屏幕扫描] 开始截图...")
    img_path = executor.screenshot()
    if not img_path:
        _debug("[屏幕扫描] 截图失败 — PowerShel 和 PIL 均无法截屏")
        _debug("[屏幕扫描] 请检查: 1) 是否有显示器连接 2) 杀毒软件是否拦截截屏")
        return []

    _debug(f"[屏幕扫描] 截图成功: {img_path} ({os.path.getsize(img_path)} bytes)")

    prompt = (
        "请仔细分析这个屏幕截图，列出所有可见的交互UI元素及其位置。"
        "对于每个元素，请提供：\n"
        "1. 元素名称/描述（如'微信图标''Chrome窗口''开始菜单''任务栏搜索框'）\n"
        "2. 估算的像素坐标（屏幕分辨率通常是1920x1080，请估算每个元素中心的X,Y坐标）\n"
        "3. 元素的大致边界\n\n"
        "请以严格的JSON数组格式回复（不要markdown）：\n"
        '[{"name":"元素名","center":[x,y],"bbox":[x1,y1,x2,y2],"conf":0.9},...]\n'
        "只返回JSON数组，不要其他文字。"
    )

    try:
        response = _call_ollama_vision(img_path, prompt, config)
    except Exception as e:
        _debug(f"[屏幕扫描] _call_ollama_vision 异常: {e}\n{traceback.format_exc()}")
        return []

    _debug(f"[屏幕扫描] 原始响应({len(response)}): {response[:500]}")

    if not response:
        _debug("[屏幕扫描] Ollama 视觉返回空响应")
        return []

    result = _extract_json(response)
    if result and isinstance(result, list):
        _debug(f"[屏幕扫描] 找到 {len(result)} 个元素")
        return result

    # 有时模型返回 {"elements": [...]} 格式
    if result and isinstance(result, dict):
        for key in ("elements", "items", "uis", "ui_elements"):
            if key in result and isinstance(result[key], list):
                _debug(f"[屏幕扫描] 从 '{key}' 字段提取到 {len(result[key])} 个元素")
                return result[key]

    _debug(f"[屏幕扫描] 无法解析为元素列表")
    return []


def match_and_plan(intent: dict, elements: list, config: dict = None) -> list:
    """
    Step 3: 用 DeepSeek 匹配语义目标与屏幕元素，生成可执行计划
    返回: [{"action":"click","x":140,"y":230,"target":"微信图标","note":"..."}, ...]
    """
    if config is None:
        config = _load_config()

    if not elements:
        _debug("[匹配规划] 无屏幕元素，跳过")
        return []

    system = (
        "你是一个桌面操作执行器。根据语义操作步骤和屏幕上的实际元素列表，"
        "为每个步骤匹配屏幕元素并输出可执行操作序列。\n\n"
        "规则：\n"
        "1. 匹配到的元素直接用其 center 坐标做 move_click\n"
        "2. 未匹配到的步骤用键盘替代（press_win搜索、Ctrl+F搜索、Tab导航）\n"
        "3. type_text 前必须先 move_click 输入框坐标\n"
        "4. 返回严格JSON数组（不要markdown）：\n"
        '[{"action":"move_click","x":385,"y":46,"target":"微信图标","note":"打开微信"},'
        '{"action":"wait","duration":3},'
        '{"action":"move_click","x":500,"y":100,"target":"搜索框","note":"点击搜索"},...]\n'
        "支持的action: move_click, move_double_click, type_text, press_keys, press_enter, press_win, press_escape, focus_window, wait"
    )

    prompt = (
        f"语义步骤：\n{json.dumps(intent, ensure_ascii=False, indent=2)}\n\n"
        f"屏幕元素（使用这些坐标）：\n{json.dumps(elements, ensure_ascii=False, indent=2)}\n\n"
        "请匹配生成可执行计划（JSON数组）。匹配到的用move_click坐标，匹配不到的用键盘。"
    )

    _debug(f"[匹配规划] 开始匹配，{len(elements)} 个元素...")
    response = _call_deepseek(prompt, config, system, max_tokens=4096)
    _debug(f"[匹配规划] 原始响应({len(response)}): {response[:500]}")

    if not response:
        _debug("[匹配规划] DeepSeek 返回空响应")
        return []

    result = _extract_json(response)
    if result and isinstance(result, list):
        _debug(f"[匹配规划] 生成 {len(result)} 个执行步骤")
        return result

    _debug("[匹配规划] 无法解析为执行计划")
    return []


def _plan_from_elements(user_cmd: str, elements: list, config: dict = None) -> list:
    """
    降级模式：语义理解失败但视觉可用时，跳过语义分解，
    将 user_cmd + 屏幕元素一起发给 DeepSeek，一步生成可执行计划。
    """
    if config is None:
        config = _load_config()

    _debug("[规划回退] 语义理解失败但视觉可用，直接从指令+元素生成计划...")

    system = (
        "你是一个 Windows 桌面自动化执行专家。你需要根据用户指令和屏幕上识别出的UI元素，"
        "生成真实鼠标点击+键盘配合的操作序列。\n\n"
        "策略：\n"
        "1. 屏幕上已有目标元素 → 直接用 move_click 点击其坐标（center字段）\n"
        "2. 目标元素不在屏幕上 → 用 press_win + type_text + Enter 搜索启动\n"
        "3. 输入文字前必须先用 move_click 点击输入框的坐标\n"
        "4. 发送消息用 press_enter，不要点击发送按钮（按钮坐标不可靠时 Enter 更稳）\n"
        "5. 每个操作后留适当等待时间\n\n"
        "返回严格JSON数组（不要markdown）：\n"
        '[{"action":"move_click","x":385,"y":46,"target":"微信图标","note":"点击微信图标"},'
        '{"action":"wait","duration":3,"note":"等待微信窗口加载"},'
        '{"action":"press_keys","keys":"^f","note":"Ctrl+F搜索"},...]\n\n'
        "支持的action类型：\n"
        "- move_click: 移动鼠标并点击（需要x,y,target，核心操作）\n"
        "- move_double_click: 移动并双击（需要x,y,target）\n"
        "- type_text: 输入文字（需要text字段，输入前确保已点击目标输入框）\n"
        "- press_keys: 组合键（keys字段如 '^f'=Ctrl+F, '%{TAB}'=Alt+Tab, '^v'=Ctrl+V, '{ENTER}'=回车）\n"
        "- press_enter: 按回车\n"
        "- press_win: 按Win键打开开始菜单\n"
        "- press_escape: 按Esc\n"
        "- wait: 等待（duration字段，单位秒）"
    )

    prompt = (
        f"用户指令：{user_cmd}\n\n"
        f"屏幕上的UI元素（使用这些坐标来点击）：\n{json.dumps(elements, ensure_ascii=False, indent=2)}\n\n"
        "请生成可执行操作计划（JSON数组）。屏幕上有的元素直接用move_click点坐标，没有的用键盘搜索。"
    )

    response = _call_deepseek(prompt, config, system, max_tokens=4096)
    _debug(f"[规划回退] 响应({len(response)}): {response[:500]}")

    if not response:
        _debug("[规划回退] DeepSeek 返回空响应")
        return []

    result = _extract_json(response)
    if result and isinstance(result, list):
        _debug(f"[规划回退] 生成 {len(result)} 个执行步骤")
        return result

    _debug("[规划回退] 无法解析为执行计划")
    return []


def _plan_keyboard_only(intent: dict, user_cmd: str, config: dict = None) -> list:
    """
    降级模式：Ollama 视觉不可用时，用 DeepSeek 生成纯键盘操作计划。
    不依赖屏幕坐标，只用快捷键、窗口操作、文本输入。
    """
    if config is None:
        config = _load_config()

    _debug("[降级] 视觉不可用，使用纯键盘模式规划...")

    system = (
        "你是一个 Windows 桌面自动化专家。当前视觉系统不可用，你只能使用键盘操作。\n\n"
        "Windows 快捷键知识：\n"
        "- Win 键打开开始菜单，输入文字可搜索应用/文件\n"
        "- Win+D 显示桌面，Win+E 打开资源管理器\n"
        "- Win+R 打开运行对话框\n"
        "- Alt+Tab 切换窗口，Ctrl+F 搜索（在大多数应用内）\n"
        "- Ctrl+C/V 复制粘贴，Ctrl+A 全选\n"
        "- Enter 确认/执行，Esc 退出/关闭\n"
        "- Tab/Shift+Tab 在界面元素间导航\n\n"
        "请为以下任务生成纯键盘操作序列，返回严格 JSON 数组（不要 markdown）：\n"
        '[{"action":"press_win","note":"打开开始菜单"},'
        '{"action":"type_text","text":"微信","note":"搜索微信"},'
        '{"action":"wait","duration":2,"note":"等待搜索结果"},'
        '{"action":"press_enter","note":"启动微信"},...]\n\n'
        "支持的 action 类型（只能使用这些）：\n"
        "- press_win: 按 Win 键\n"
        "- press_enter: 按 Enter\n"
        "- press_escape: 按 Esc\n"
        "- press_keys: 按组合键，keys 字段如 '^f' (Ctrl+F), '%{TAB}' (Alt+Tab), '^v' (Ctrl+V)\n"
        "- type_text: 输入文字，text 字段为要输入的内容\n"
        "- wait: 等待，duration 字段为秒数\n"
        "- focus_window: 聚焦窗口，title 字段为窗口标题关键词\n\n"
        "重要原则：\n"
        "1. 用 Win 键搜索启动应用是首选方式\n"
        "2. 每次操作后留足够等待时间\n"
        "3. 应用内搜索用 Ctrl+F\n"
        "4. 输入中文后必须用 Enter 确认发送\n"
        "5. 只返回 JSON 数组，不要其他文字"
    )

    prompt = (
        f"用户指令：{user_cmd}\n\n"
        f"语义理解结果：{json.dumps(intent, ensure_ascii=False, indent=2)}\n\n"
        "请为这个任务生成纯键盘操作计划（JSON数组）。"
    )

    response = _call_deepseek(prompt, config, system, max_tokens=4096)
    _debug(f"[降级] DeepSeek 响应({len(response)}): {response[:500]}")

    if not response:
        _debug("[降级] DeepSeek 返回空响应")
        return []

    result = _extract_json(response)
    if result and isinstance(result, list):
        _debug(f"[降级] 生成 {len(result)} 个键盘操作步骤")
        return result

    # 尝试从意图中直接构建简单计划
    _debug("[降级] JSON 解析失败，尝试从语义步骤构建...")
    if intent.get("steps"):
        plan = _build_keyboard_plan_from_steps(intent["steps"], user_cmd)
        if plan:
            _debug(f"[降级] 从语义步骤构建了 {len(plan)} 个步骤")
            return plan

    return []


def _build_keyboard_plan_from_steps(steps: list, user_cmd: str = "") -> list:
    """
    将语义步骤转换为纯键盘操作计划。
    覆盖所有常见的 click 目标类型，不再只处理"微信"和"搜索"两个关键词。
    """
    plan = []
    # 从 user_cmd 尝试提取应用名
    app_keywords = ["微信", "钉钉", "QQ", "浏览器", "Chrome", "Edge", "Firefox",
                    "记事本", "Word", "Excel", "PPT", "WPS", "计算器", "CMD",
                    "VSCode", "VS Code", "终端", "Terminal", "设置"]
    extracted_app = ""
    for kw in app_keywords:
        if kw.lower() in user_cmd.lower():
            extracted_app = kw
            break

    for s in steps:
        action = s.get("action", "")
        target = s.get("target", "")
        note = s.get("note", "")
        # 合并 target 和 note 做关键词匹配
        combined = f"{target} {note}".lower()

        if action in ("click", "double_click"):
            plan += _click_to_keyboard(combined, target, note, extracted_app)

        elif action in ("type", "type_text"):
            text = s.get("text", target)  # 优先用 text 字段
            if text:
                plan.append({"action": "type_text", "text": text, "note": note or f"输入 {text}"})

        elif action in ("press", "press_keys"):
            keys = s.get("keys", target)
            if keys:
                plan.append({"action": "press_keys", "keys": keys, "note": note or f"按键 {keys}"})

        elif action in ("focus", "focus_window"):
            title = s.get("title", target)
            if title:
                plan.append({"action": "focus_window", "title": title, "note": note or f"聚焦 {title}"})

        elif action == "wait":
            duration = s.get("duration", 2)
            if isinstance(duration, str):
                try:
                    duration = float(duration)
                except:
                    duration = 2
            plan.append({"action": "wait", "duration": duration, "note": note or f"等待 {duration}s"})

        elif action == "verify":
            # 验证步骤 → 短暂等待, 无法真正验证
            plan.append({"action": "wait", "duration": 1, "note": f"验证: {note or target}"})

        elif action in ("press_enter", "press_escape", "press_win"):
            plan.append({"action": action, "note": note or target})

        else:
            # 未知 action → 尝试作为通用目标用 Enter 处理
            _debug(f"[降级] 未知 action '{action}'，尝试 Enter 处理")
            plan.append({"action": "press_enter", "note": f"处理: {target}"})

    return plan


def _click_to_keyboard(combined: str, target: str, note: str, app_name: str = "") -> list:
    """
    将点击操作映射为键盘替代方案。
    覆盖所有常见目标类型。
    """
    steps = []

    # 1. 搜索/查找类 → Ctrl+F
    if any(kw in combined for kw in ["搜索", "search", "查找", "find"]):
        steps.append({"action": "press_keys", "keys": "^f", "note": f"搜索 ({target})"})
        steps.append({"action": "wait", "duration": 0.5})

    # 2. 桌面图标 / 启动应用 → Win键搜索
    elif any(kw in combined for kw in ["桌面", "图标", "快捷方式", "任务栏", "启动", "打开", "运行", "开始菜单"]):
        app = app_name or target
        steps.append({"action": "press_win", "note": "打开开始菜单"})
        steps.append({"action": "wait", "duration": 0.5})
        steps.append({"action": "type_text", "text": app, "note": f"搜索 {app}"})
        steps.append({"action": "wait", "duration": 2})
        steps.append({"action": "press_enter", "note": f"启动 {app}" if app_name else "确认"})

    # 3. 输入框/文本框 → 不需要额外操作，后续 type_text 会自动聚焦
    elif any(kw in combined for kw in ["输入框", "输入", "文本框", "text", "input", "编辑", "消息框", "聊天框"]):
        steps.append({"action": "wait", "duration": 0.3, "note": f"准备输入 ({target})"})

    # 4. 发送/确认/OK/提交 → Enter
    elif any(kw in combined for kw in ["发送", "确认", "确定", "提交", "ok", "完成", "回车", "send", "submit", "按钮", "button"]):
        steps.append({"action": "press_enter", "note": f"点击 {target}"})

    # 5. 联系人/聊天/会话/结果 → Enter 选择
    elif any(kw in combined for kw in ["联系人", "聊天", "会话", "结果", "好友", "群", "contact", "chat", "result"]):
        steps.append({"action": "wait", "duration": 1, "note": f"等待 {target} 出现"})
        steps.append({"action": "press_enter", "note": f"选择 {target}"})

    # 6. 窗口/应用名 → 尝试 Win+搜索启动 或 Alt+Tab
    elif any(kw in combined for kw in ["窗口", "window", "应用", "程序"]):
        if app_name:
            steps.append({"action": "press_win", "note": "打开开始菜单"})
            steps.append({"action": "wait", "duration": 0.5})
            steps.append({"action": "type_text", "text": app_name})
            steps.append({"action": "wait", "duration": 2})
            steps.append({"action": "press_enter"})
        else:
            steps.append({"action": "press_keys", "keys": "%{TAB}", "note": f"切换窗口 ({target})"})

    # 7. 菜单/选项/标签/Tab → Tab 导航
    elif any(kw in combined for kw in ["菜单", "选项", "标签", "tab", "menu", "option", "设置", "偏好"]):
        steps.append({"action": "press_keys", "keys": "{TAB}", "note": f"导航到 {target}"})

    # 8. 关闭/取消/退出/返回 → Esc
    elif any(kw in combined for kw in ["关闭", "取消", "退出", "返回", "取消", "close", "cancel", "back"]):
        steps.append({"action": "press_escape", "note": f"关闭/取消 ({target})"})

    # 9. 通用回退：有 app_name → Win 搜索；否则 → Enter（最通用）
    else:
        if app_name:
            steps.append({"action": "press_win", "note": "打开开始菜单"})
            steps.append({"action": "wait", "duration": 0.5})
            steps.append({"action": "type_text", "text": app_name})
            steps.append({"action": "wait", "duration": 2})
            steps.append({"action": "press_enter", "note": f"启动 {app_name}"})
        else:
            # 最通用：用 Tab 导航 + Enter
            steps.append({"action": "press_keys", "keys": "{TAB}", "note": f"导航 ({target})"})
            steps.append({"action": "wait", "duration": 0.5})
            steps.append({"action": "press_enter", "note": f"确认 ({target})"})

    return steps


def execute_plan(plan: list, progress_cb=None, config: dict = None) -> str:
    """
    Step 4: 执行操作计划
    progress_cb(status, step_index, total_steps) 在每个步骤前后调用
    返回最终报告
    """
    if config is None:
        config = _load_config()

    exe_cfg = config.get("execution", {})
    delay = exe_cfg.get("step_delay_ms", 500) / 1000.0
    max_retries = exe_cfg.get("max_retries", 3)

    if not plan:
        _debug("[执行] 计划为空，跳过")
        return "⚠ 无操作步骤可执行"

    total = len(plan)
    report_lines = []

    for i, step in enumerate(plan):
        action = step.get("action", "click")
        target = step.get("target", step.get("note", "未知目标"))
        note = step.get("note", "")

        status = f"[{i+1}/{total}] {action}: {target}"
        if progress_cb:
            progress_cb(status, i, total)

        success = False
        for attempt in range(max_retries):
            try:
                if action in ("move_click", "click"):
                    x, y = step.get("x", 0), step.get("y", 0)
                    if x and y:
                        success = executor.click(x, y)
                    else:
                        success = False

                elif action in ("move_double_click", "double_click"):
                    x, y = step.get("x", 0), step.get("y", 0)
                    if x and y:
                        success = executor.double_click(x, y)
                    else:
                        success = False

                elif action in ("type_text", "type"):
                    text = step.get("text", step.get("target", ""))
                    if text:
                        # 如果目标不是文字而是元素名，先点击再输入
                        x, y = step.get("x", 0), step.get("y", 0)
                        if x and y:
                            executor.click(x, y)
                            executor.wait(0.3)
                        success = executor.type_text(text)
                    else:
                        success = False

                elif action in ("press_keys", "press"):
                    keys = step.get("keys", step.get("target", ""))
                    if keys:
                        success = executor.press_keys(keys)
                    else:
                        success = False

                elif action in ("focus_window", "focus"):
                    title = step.get("title", target)
                    success = executor.focus_window(title)

                elif action == "wait":
                    duration = step.get("duration", 1.0)
                    executor.wait(duration)
                    success = True

                elif action == "press_enter":
                    success = executor.press_enter()

                elif action == "press_escape":
                    success = executor.press_escape()

                elif action == "press_win":
                    success = executor.press_win()

                else:
                    # 尝试作为通用目标处理
                    x, y = step.get("x", 0), step.get("y", 0)
                    if x and y:
                        success = executor.click(x, y)
                    else:
                        success = False

                if success:
                    break

            except Exception as e:
                _debug(f"[执行] 步骤 {i+1} 尝试 {attempt+1} 异常: {e}")
                if progress_cb:
                    progress_cb(f"  重试 {attempt+1}: {e}", i, total)
                executor.wait(0.5)

        marker = "✓" if success else "✗"
        msg = f"{marker} [{i+1}/{total}] {action}: {target}"
        if note:
            msg += f" ({note})"
        report_lines.append(msg)

        if not success:
            report_lines.append(f"  ⚠ 该步骤失败（{max_retries}次重试后）")

        executor.wait(delay)

    return "\n".join(report_lines)


# ===== 视觉反馈闭环（单步决策） =====

def _analyze_screen(img_path: str, user_cmd: str, config: dict = None) -> list:
    """
    分析当前屏幕截图，返回可交互元素列表。
    每次迭代都重新截图分析，获取最新屏幕状态。
    """
    if config is None:
        config = _load_config()

    if not img_path or not os.path.exists(img_path):
        return []

    prompt = (
        "分析这个Windows桌面截图。列出所有可点击交互的UI元素及其像素坐标。"
        "屏幕分辨率约1920x1080。重点识别：\n"
        "- 任务栏图标和应用按钮（微信、QQ、Chrome、文件管理器等）\n"
        "- 桌面快捷方式图标\n"
        "- 打开的窗口标题栏和内容区域\n"
        "- 对话框中的按钮（确认、取消、登录、进入等）\n"
        "- 输入框、搜索框、文本框\n"
        "- 文本标签和菜单项\n"
        "- 任何可点击的按钮和链接\n\n"
        "返回严格JSON数组（不要markdown，不要尾部逗号）：\n"
        '[{"name":"微信图标","center":[x,y],"bbox":[x1,y1,x2,y2],"conf":0.9},...]'
    )

    response = _call_ollama_vision(img_path, prompt, config)
    _debug(f"[屏幕分析] 原始({len(response)}字符): {response[:300]}")

    if not response:
        return []

    result = _extract_json(response)
    if result and isinstance(result, list):
        return result

    if result and isinstance(result, dict):
        for key in ("elements", "items", "uis", "ui_elements"):
            if key in result and isinstance(result[key], list):
                return result[key]

    return []


def _execute_single_action(step: dict) -> bool:
    """执行单个操作步骤，返回是否成功"""
    action = step.get("action", "wait")

    try:
        if action in ("move_click", "click"):
            x, y = step.get("x", 0), step.get("y", 0)
            if x and y:
                return executor.click(x, y)
            return False

        elif action in ("move_double_click", "double_click"):
            x, y = step.get("x", 0), step.get("y", 0)
            if x and y:
                return executor.double_click(x, y)
            return False

        elif action in ("type_text", "type"):
            text = step.get("text", step.get("target", ""))
            if text:
                x, y = step.get("x", 0), step.get("y", 0)
                if x and y:
                    executor.click(x, y)
                    executor.wait(0.3)
                return executor.type_text(text)
            return False

        elif action in ("press_keys", "press"):
            keys = step.get("keys", step.get("target", ""))
            if keys:
                return executor.press_keys(keys)
            return False

        elif action == "press_enter":
            return executor.press_enter()

        elif action == "press_win":
            return executor.press_win()

        elif action == "press_escape":
            return executor.press_escape()

        elif action in ("focus_window", "focus"):
            title = step.get("title", step.get("target", ""))
            if title:
                return executor.focus_window(title)
            return False

        elif action == "wait":
            duration = step.get("duration", 1.0)
            executor.wait(duration)
            return True

        else:
            x, y = step.get("x", 0), step.get("y", 0)
            if x and y:
                return executor.click(x, y)
            return False

    except Exception as e:
        _debug(f"[单步执行] 异常: {e}")
        return False


def _decide_next_action(user_cmd: str, goal: str, screen_elements: list,
                        history: list, iteration: int, config: dict = None) -> dict:
    """
    基于当前屏幕状态和操作历史，决定下一步单个操作。
    这是视觉闭环的核心：看着屏幕，逐步决策。
    """
    if config is None:
        config = _load_config()

    _debug(f"[视觉决策] 第{iteration}步，屏幕{len(screen_elements)}元素，历史{len(history)}步")

    system = (
        "你是一个桌面自动化操作员，正看着用户的Windows桌面执行任务。\n"
        "你的工作方式：看一眼屏幕 → 做一个操作 → 再看一眼屏幕 → 再做下一个操作。\n\n"
        "核心规则：\n"
        "1. 只输出 ONE 个操作（不是一个计划）\n"
        "2. 严格根据当前屏幕上的元素来决策，不要假设屏幕上有你看不到的东西\n"
        "3. 如果当前屏幕没有目标元素，用键盘（Win键、Ctrl+F、Tab等）\n"
        "4. 发现任务已经完成 → 输出 {\"done\":true}\n"
        "5. 卡住时（同一个操作失败了）→ 换一种完全不同的方法\n\n"
        "返回严格JSON（不要markdown，单行）：\n"
        '做操作时: {"action":"move_click","x":100,"y":200,"target":"微信图标","note":"点击微信图标","done":false}\n'
        '完成任务时: {"done":true,"summary":"已成功发送消息"}\n\n'
        "支持的action: move_click(x,y,target), move_double_click(x,y,target), "
        "type_text(text), press_keys(keys), press_enter, press_win, press_escape, "
        "focus_window(title), wait(duration)"
    )

    # 构建历史文本
    if history:
        history_lines = []
        for h in history[-8:]:  # 最近8步
            marker = "+" if h.get("success") else "-"
            history_lines.append(
                f"  [{marker}] {h.get('action','?')}: {h.get('note','?')}"
            )
        # 添加当前屏幕信息到历史记录
        if history and history[-1].get("elements_names"):
            history_lines.append(f"  屏幕上有: {', '.join(history[-1]['elements_names'][:6])}")
        history_text = "\n".join(history_lines)
    else:
        history_text = "  (首次操作，尚未执行任何步骤)"

    prompt = (
        f"任务目标：{user_cmd}\n"
        f"理解：{goal}\n\n"
        f"【当前屏幕上的元素】\n{json.dumps(screen_elements, ensure_ascii=False, indent=2)}\n\n"
        f"【已执行的操作历史】\n{history_text}\n\n"
        f"现在是第{iteration}次操作。请观察当前屏幕，输出下一步操作。"
    )

    response = _call_deepseek(prompt, config, system, max_tokens=2048)
    _debug(f"[视觉决策] 响应({len(response)}): {response[:300]}")

    if not response:
        return {"action": "wait", "duration": 1, "note": "API无响应", "done": False}

    result = _extract_json(response)
    if result and isinstance(result, dict):
        if result.get("done"):
            _debug(f"[视觉决策] 完成: {result.get('summary','')}")
            return result
        action = result.get("action", "wait")
        note = result.get("note", "")
        _debug(f"[视觉决策] 下一步: {action}({note})")
        return result

    _debug(f"[视觉决策] 解析失败: {response[:200]}")
    return {"action": "wait", "duration": 1, "note": "决策解析失败", "done": False}


def run_visual_loop(user_cmd: str, progress_cb=None, config: dict = None) -> str:
    """
    视觉反馈闭环管道（新主模式）：
    语义理解 → [截屏→分析→决策→操作] × N → 完成
    每次迭代重新截图分析，逐步逼近目标。
    """
    if config is None:
        config = _load_config()

    _debug(f"{'='*60}")
    _debug(f"视觉闭环启动: {user_cmd[:100]}")

    ts_dir = os.path.join(SCREENSHOTS_DIR, time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(ts_dir, exist_ok=True)

    log = []
    t0 = time.time()

    # === Step 1: 语义理解（一次性） ===
    if progress_cb:
        progress_cb("🧠 语义理解...", 0, 0)
    intent = understand_intent(user_cmd, config)
    goal = intent.get("goal", user_cmd[:30])
    log.append(f"[语义理解] 目标: {goal}")
    log.append(f"  规划步骤数: {len(intent.get('steps',[]))}")
    _debug(f"[视觉闭环] 语义理解: {goal}")

    # === Step 2: 视觉反馈闭环 ===
    max_iterations = 25
    history = []
    done = False
    summary = ""

    for i in range(1, max_iterations + 1):
        _debug(f"[视觉闭环] === 迭代 {i}/{max_iterations} ===")

        # 2a. 截图
        if progress_cb:
            progress_cb(f"📷 截屏 ({i})...", i, max_iterations)
        img_path = executor.screenshot()
        if not img_path:
            log.append(f"[{i}] 截图失败，重试...")
            _debug(f"[视觉闭环] 迭代{i} 截图失败")
            executor.wait(1)
            continue

        # 保存截图
        try:
            import shutil
            shutil.copy(img_path, os.path.join(ts_dir, f"iter{i:02d}_{time.strftime('%H%M%S')}.png"))
        except:
            pass

        # 2b. 分析屏幕
        if progress_cb:
            progress_cb(f"👁 分析屏幕 ({i})...", i, max_iterations)
        elements = _analyze_screen(img_path, user_cmd, config)
        log.append(f"[{i}] 找到 {len(elements)} 个元素")
        el_names = [e.get("name", "?") for e in elements[:5]]
        _debug(f"[视觉闭环] 迭代{i} 元素: {el_names}")

        if progress_cb and elements:
            progress_cb(f"👁 看到: {', '.join(el_names[:3])}", i, max_iterations)

        # 2c. 决策下一步
        if progress_cb:
            progress_cb(f"🤔 决策 ({i})...", i, max_iterations)
        decision = _decide_next_action(user_cmd, goal, elements, history, i, config)

        if decision.get("done"):
            done = True
            summary = decision.get("summary", "任务完成")
            log.append(f"[{i}] ✅ {summary}")
            _debug(f"[视觉闭环] 完成: {summary}")
            break

        # 2d. 执行操作
        action_name = decision.get("action", "?")
        action_note = decision.get("note", "")

        if progress_cb:
            progress_cb(f"⚡ {action_note}", i, max_iterations)

        success = _execute_single_action(decision)
        marker = "+" if success else "-"
        log.append(f"[{i}] {marker} {action_name}: {action_note}")
        _debug(f"[视觉闭环] 迭代{i}: {action_name}({action_note}) → {'OK' if success else 'FAIL'}")

        history.append({
            "i": i,
            "action": action_name,
            "note": action_note,
            "success": success,
            "elements_count": len(elements),
            "elements_names": el_names
        })

        # 操作后等待
        delay = config.get("execution", {}).get("step_delay_ms", 500) / 1000.0
        executor.wait(max(delay, 0.5))

        # 卡死检测：连续3次相同操作 → 注入提示
        if len(history) >= 3:
            last3 = history[-3:]
            if (all(h["action"] == last3[0]["action"] for h in last3) and
                    not any(h["success"] for h in last3)):
                _debug("[视觉闭环] 连续3次失败，注入换策略提示")
                history.append({
                    "i": i + 0.5, "action": "system",
                    "note": "⚠ 连续3次相同操作失败！请换完全不同的方案",
                    "success": True, "elements_count": 0, "elements_names": []
                })

    # === 最终报告 ===
    elapsed = time.time() - t0
    if done:
        log.append(f"\n✅ 视觉闭环完成 ({elapsed:.0f}s, {len(history)}步)")
    else:
        log.append(f"\n⚠ 达到最大迭代 ({max_iterations}次)，任务可能未完成")
    log.append(f"[语义理解] 目标: {goal}")
    log.append(f"[执行统计] {len(history)} 次操作, {sum(1 for h in history if h.get('success'))} 成功")

    report = "\n".join(log)
    _debug(f"视觉闭环结束，{elapsed:.1f}s, {len(history)}步")
    return report


# ===== Claude Code 桥接 =====

CLAUDE_BRIDGE = os.path.join(_BLUE_DIR, "claude_bridge.py")


def _call_claude_code(prompt: str, timeout: int = 300, image_paths: list = None) -> dict:
    """
    通过 claude_bridge.py 调用 Claude Code CLI。
    image_paths: 可选，图片路径列表
    返回: {"ok": bool, "reply": str, "elapsed": float}
    """
    _debug(f"[Claude桥接] 调用: {prompt[:100]}...")
    if image_paths:
        _debug(f"[Claude桥接] 附带 {len(image_paths)} 张图片")

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"

        # 构建命令行：只传 --image 参数，prompt 走 stdin（突破 8191 字符限制）
        cmd = ["python", CLAUDE_BRIDGE]
        for ip in (image_paths or []):
            cmd.extend(["--image", ip])

        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,           # prompt 从 stdin 传入
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace",
            cwd=WORK, env=env,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        out, err = p.communicate(input=prompt, timeout=timeout + 10)
        out = (out or "").strip()
        err = (err or "").strip()

        _debug(f"[Claude桥接] stdout({len(out)}): {out[:200]}")
        if err:
            _debug(f"[Claude桥接] stderr: {err[:300]}")

        # 解析 JSON 结果
        import json as _json
        try:
            result = _json.loads(out)
            if result.get("ok"):
                _debug(f"[Claude桥接] 成功, {len(result.get('reply',''))}字符, {result.get('elapsed',0)}s")
            else:
                _debug(f"[Claude桥接] 失败: {result.get('error','?')}")
            return result
        except _json.JSONDecodeError:
            # 如果不是 JSON，直接当文本返回
            if out:
                return {"ok": True, "reply": out, "elapsed": 0}
            return {"ok": False, "error": f"无法解析桥接输出: {out[:200]}"}

    except subprocess.TimeoutExpired:
        p.kill()
        _debug("[Claude桥接] 超时")
        return {"ok": False, "error": "Claude Code 超时"}
    except Exception as e:
        _debug(f"[Claude桥接] 异常: {e}")
        return {"ok": False, "error": str(e)}


def run_claude(prompt: str, progress_cb=None, config: dict = None, image_paths: list = None) -> str:
    """
    Claude 模式入口 — 直接把指令发给 Claude Code，返回回复。
    适用于编程、问答、文件操作等非桌面自动化任务。
    image_paths: 可选，图片路径列表（支持视觉分析）
    """
    _debug(f"{'='*60}")
    _debug(f"Claude模式启动: {prompt[:100]}")
    if image_paths:
        _debug(f"Claude模式: 附带 {len(image_paths)} 张图片")

    if progress_cb:
        progress_cb("🤖 调用 Claude Code...", 0, 1)

    result = _call_claude_code(prompt, image_paths=image_paths)

    if progress_cb:
        progress_cb("✅ Claude 回复完成", 1, 1)

    if result.get("ok"):
        elapsed = result.get("elapsed", 0)
        reply = result["reply"]
        return f"[Claude Code · {elapsed:.0f}s]\n{reply}"
    else:
        return f"❌ Claude Code 调用失败: {result.get('error', '未知错误')}"


# ===== 主入口 =====

def run(user_cmd: str, progress_cb=None, config: dict = None, image_paths: list = None) -> str:
    """
    知新管道主入口 — 全部走 Claude Code
    旧的桌面自动化代码保留但不再调用。
    image_paths: 可选，图片路径列表（支持视觉分析）
    """
    if config is None:
        config = _load_config()

    # 清理旧调试日志
    try:
        if os.path.exists(DEBUG_LOG) and os.path.getsize(DEBUG_LOG) > 5 * 1024 * 1024:
            os.remove(DEBUG_LOG)
    except:
        pass

    # 去掉 /c 前缀（兼容旧习惯），全部走 Claude
    prompt = user_cmd.strip()
    for prefix in ("/claude ", "/c ", "/claude", "/c"):
        if prompt.lower().startswith(prefix):
            prompt = prompt[len(prefix):].strip()
            break
    if not prompt:
        return "❌ 请提供指令"

    _debug(f"{'='*60}")
    _debug(f"Claude模式: {prompt[:100]}")
    return run_claude(prompt, progress_cb, config, image_paths=image_paths)


# ===== 流式入口 =====

def run_stream(user_cmd: str, on_text=None, on_done=None,
               config: dict = None, image_paths: list = None,
               file_paths: list = None, timeout: int = 300) -> None:
    """
    流式聊天入口 — 直接调用 Claude Code CLI 的 stream-json 输出。
    适用于简单对话（非桌面自动化任务）。

    on_text(str)   — 每收到一段 delta 文本回调
    on_done(dict)  — 流结束回调: {"ok": bool, "elapsed": float, "error": str|None}
    """
    if config is None:
        config = _load_config()

    prompt = user_cmd.strip()
    if not prompt:
        if on_done:
            on_done({"ok": False, "error": "请提供指令", "elapsed": 0})
        return

    # 文件/图片附加到 prompt
    if file_paths:
        prompt += "\n\n---\n用户提供了以下文件，请使用 Read 工具逐个读取并分析：\n"
        for fp in file_paths:
            prompt += f"\n- {fp}"
        prompt += "\n\n请读取上述所有文件后再回复用户。\n---"

    # 如果有网页搜索指令，提示 Claude 使用 WebSearch
    if prompt.strip().startswith("🔍"):
        prompt = prompt.strip()[2:].strip()
        prompt = "Please use WebSearch to search the web for relevant information before answering.\n\n" + prompt

    _debug(f"[流式] 启动: {prompt[:100]}")

    try:
        import claude_bridge
        claude_bridge.call_claude_stream(
            prompt, timeout=timeout, image_paths=image_paths,
            on_text=on_text, on_done=on_done
        )
    except Exception as e:
        _debug(f"[流式] 异常: {e}")
        if on_done:
            on_done({"ok": False, "error": str(e), "elapsed": 0})
