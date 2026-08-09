"""测试 Claude Code 桥接 — 单文件，无依赖"""
import subprocess, json, os, time

_BLUE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(_BLUE_DIR)
BRIDGE = os.path.join(_BLUE_DIR, "claude_bridge.py")

t0 = time.time()
print("调用 Claude Code...")
p = subprocess.run(
    ["python", BRIDGE, "用Python写一个Hello World，只输出代码不要解释"],
    capture_output=True, encoding="utf-8", timeout=120,
    cwd=WORK, creationflags=subprocess.CREATE_NO_WINDOW
)
elapsed = time.time() - t0

result = json.loads(p.stdout.strip())
if result["ok"]:
    print(f"✅ 成功 ({elapsed:.0f}s):\n{result['reply'][:500]}")
else:
    print(f"❌ 失败: {result['error']}")
