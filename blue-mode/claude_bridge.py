"""
老六 ↔ Claude Code 桥接器
老六通过此脚本发送指令给 Claude Code，并获取回复

用法:
    python claude_bridge.py "你的指令"
    python claude_bridge.py --image path.png "你的指令"   # 带图片
    python claude_bridge.py --file task.txt      # 从文件读指令
    python claude_bridge.py --chat               # 交互模式

返回格式 (JSON):
    {"ok": true, "reply": "Claude 的回复...", "elapsed": 12.3}
    {"ok": false, "error": "错误信息"}
"""
import subprocess
import json
import sys
import os
import time

_BLUE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(_BLUE_DIR)
NODE = os.path.join(WORK, "nodejs")
LOG_FILE = os.path.join(_BLUE_DIR, "claude_bridge.log")


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass


def find_claude() -> str | None:
    """找到 claude 命令的路径"""
    candidates = [
        os.path.join(NODE, "claude.cmd"),
        os.path.join(WORK, r"node_modules\.bin\claude.cmd"),
    ]

    # 检测 npm 全局安装路径
    for npm_dir in _get_npm_global_dirs():
        candidates.append(os.path.join(npm_dir, "claude.cmd"))
        candidates.append(os.path.join(npm_dir, "claude.ps1"))

    candidates.append("claude")

    for c in candidates:
        if not c:
            continue
        try:
            r = subprocess.run(
                [c, "--version"], capture_output=True,
                encoding="utf-8", timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if r.returncode == 0:
                return c
        except:
            continue
    return None


def _get_npm_global_dirs() -> list:
    """获取 npm 全局安装目录的候选列表"""
    dirs = []
    # 方法1: npm prefix -g（可能不在 PATH 中）
    try:
        r = subprocess.run(
            ["cmd", "/c", "npm", "prefix", "-g"], capture_output=True,
            encoding="utf-8", timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if r.returncode == 0 and r.stdout.strip():
            dirs.append(r.stdout.strip())
    except:
        pass
    # 方法2: 常见路径（覆盖大多数用户安装场景）
    for drive in ["D:", "C:", "E:"]:
        root = drive + "\\"
        dirs.append(os.path.join(root, "npm-global"))
        dirs.append(os.path.join(root, "npm"))
    # 方法3: APPDATA
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        dirs.append(os.path.join(appdata, "npm"))
    return dirs


def call_claude(prompt: str, timeout: int = 300, image_paths: list = None) -> dict:
    """
    调用 Claude Code，返回 {"ok": bool, "reply": str, "elapsed": float}

    image_paths: 可选，图片路径列表，作为 --image 参数传给 Claude Code CLI
    """
    claude = find_claude()
    if not claude:
        return {"ok": False, "error": "找不到 claude 命令，请确认 Claude Code 已安装"}

    log(f"调用 Claude: {prompt[:100]}...")
    if image_paths:
        log(f"  附带 {len(image_paths)} 张图片")

    env = os.environ.copy()
    env["NODE_HOME"] = NODE
    env["PATH"] = NODE + ";" + os.path.join(WORK, r"node_modules\.bin") + ";" + env.get("PATH", "")
    env["OPENCLAW_HOME"] = WORK
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"

    # 构建命令：--image 参数放在 -p 前面
    cmd = [claude]
    for ip in (image_paths or []):
        cmd.extend(["--image", ip])
    cmd.extend(["-p", prompt, "--dangerously-skip-permissions"])

    t0 = time.time()
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace",
            cwd=WORK, env=env,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        out, err = p.communicate(timeout=timeout)
        elapsed = time.time() - t0

        reply = (out or "").strip()
        err_text = (err or "").strip()

        # Claude Code CLI 可能把正常输出放到 stderr
        if not reply and err_text:
            reply = err_text

        log(f"Claude 回复 ({len(reply)}字符, {elapsed:.1f}s)")

        return {
            "ok": p.returncode == 0 or len(reply) > 0,
            "reply": reply,
            "elapsed": round(elapsed, 1)
        }

    except subprocess.TimeoutExpired:
        p.kill()
        elapsed = time.time() - t0
        return {"ok": False, "error": f"Claude 超时 ({timeout}s)", "elapsed": round(elapsed, 1)}
    except Exception as e:
        elapsed = time.time() - t0
        return {"ok": False, "error": str(e), "elapsed": round(elapsed, 1)}


def main():
    # 强制 UTF-8 输出，防止中文乱码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    image_paths = []
    prompt_args = []

    # 解析 --image 参数
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--image" and i + 1 < len(sys.argv):
            image_paths.append(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--chat":
            # 交互模式
            print("老六 ↔ Claude Code 交互模式")
            print("输入指令，Claude 回复后继续，输入 /quit 退出")
            print("-" * 50)
            while True:
                try:
                    user_input = input("\n你> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not user_input:
                    continue
                if user_input.lower() in ("/quit", "/exit", "/q"):
                    break
                result = call_claude(user_input, image_paths=image_paths if image_paths else None)
                image_paths.clear()
                if result["ok"]:
                    print(f"\nClaude ({result['elapsed']}s):\n{result['reply']}")
                else:
                    print(f"\n错误: {result['error']}")
            sys.exit(0)
        elif sys.argv[i] == "--file" and i + 1 < len(sys.argv):
            with open(sys.argv[i + 1], "r", encoding="utf-8") as f:
                prompt = f.read().strip()
            result = call_claude(prompt, image_paths=image_paths if image_paths else None)
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(0)
        else:
            prompt_args.append(sys.argv[i])
            i += 1

    if not prompt_args:
        # 无参数：从 stdin 读
        prompt = sys.stdin.read().strip()
        if not prompt:
            print(json.dumps({"ok": False, "error": "无指令输入"}, ensure_ascii=False))
            sys.exit(1)
    else:
        prompt = " ".join(prompt_args)

    result = call_claude(prompt, image_paths=image_paths if image_paths else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
