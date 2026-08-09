"""
温故 (Review Past) — 截图知识库自学习系统
- 每0.5小时：从截图学习按钮位置
- 每1.5小时：复盘验证已学知识
- 每3小时：清理已处理截图
"""
import json
import os
import time
import threading
import shutil

# 路径：基于脚本位置，不再硬编码
_BLUE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(_BLUE_DIR)
KNOWLEDGE_DIR = os.path.join(_BLUE_DIR, "knowledge")
KNOWLEDGE_FILE = os.path.join(KNOWLEDGE_DIR, "positions.json")
SCREENSHOTS_DIR = os.path.join(_BLUE_DIR, "screenshots")
ARCHIVE_DIR = os.path.join(SCREENSHOTS_DIR, "_archived")
LOG_FILE = os.path.join(_BLUE_DIR, "wengu.log")


def _log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


class WenGu:
    def __init__(self):
        self.running = False
        self.last_learn = None
        self.last_review = None
        self.last_cleanup = None
        self._thread = None
        self._lock = threading.Lock()

        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        os.makedirs(ARCHIVE_DIR, exist_ok=True)

        # 初始化知识库
        if not os.path.exists(KNOWLEDGE_FILE):
            self._save_knowledge({
                "version": 1,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "elements": {},
                "patterns": {}
            })

    def _load_knowledge(self) -> dict:
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"version": 1, "elements": {}, "patterns": {}}

    def _save_knowledge(self, data: dict):
        data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        # 先验证
        if not self._validate_knowledge(data):
            _log("VALIDATE FAILED — 知识库数据校验不通过，拒绝写入")
            return False
        with self._lock:
            try:
                tmp = KNOWLEDGE_FILE + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, KNOWLEDGE_FILE)
                return True
            except Exception as e:
                _log(f"保存知识库失败: {e}")
                return False

    def _validate_knowledge(self, data: dict) -> bool:
        """验证知识库数据完整性"""
        try:
            assert isinstance(data, dict), "data must be dict"
            assert "version" in data, "missing version"
            assert "elements" in data, "missing elements"
            assert isinstance(data["elements"], dict), "elements must be dict"
            # 验证每个元素的格式
            for name, info in data["elements"].items():
                assert isinstance(name, str), f"element name must be str: {name}"
                assert isinstance(info, dict), f"element info must be dict: {name}"
                if "bbox" in info:
                    b = info["bbox"]
                    assert isinstance(b, list) and len(b) == 4, f"bbox must be [x1,y1,x2,y2]: {name}"
                    assert all(isinstance(v, (int, float)) for v in b), f"bbox values must be numbers: {name}"
                if "center" in info:
                    c = info["center"]
                    assert isinstance(c, list) and len(c) == 2, f"center must be [x,y]: {name}"
            return True
        except AssertionError as e:
            _log(f"知识库验证错误: {e}")
            return False

    def start(self):
        """启动后台调度线程"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._scheduler, daemon=True)
        self._thread.start()
        _log("温故调度器已启动")

    def stop(self):
        """停止调度"""
        self.running = False
        _log("温故调度器已停止")

    def _scheduler(self):
        """主调度循环 — 每60秒检查一次时间"""
        while self.running:
            now = time.time()

            # 每0.5小时：学习
            if self.last_learn is None or (now - self.last_learn) >= 1800:
                try:
                    self.learn()
                except Exception as e:
                    _log(f"learn() 异常: {e}")
                self.last_learn = now

            # 每1.5小时：复盘
            if self.last_review is None or (now - self.last_review) >= 5400:
                try:
                    self.review()
                except Exception as e:
                    _log(f"review() 异常: {e}")
                self.last_review = now

            # 每3小时：清理
            if self.last_cleanup is None or (now - self.last_cleanup) >= 10800:
                try:
                    self.cleanup()
                except Exception as e:
                    _log(f"cleanup() 异常: {e}")
                self.last_cleanup = now

            time.sleep(60)

    def learn(self) -> dict:
        """
        扫描 screenshots/ 中的新截图 → 提取按钮位置 → 写入 knowledge/positions.json
        返回本次学习到的元素
        """
        _log("📚 开始学习...")

        # 收集未处理的截图
        screenshots = []
        for root, dirs, files in os.walk(SCREENSHOTS_DIR):
            if "_archived" in root:
                continue
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    screenshots.append(os.path.join(root, f))

        if not screenshots:
            _log("  无新截图可学习")
            return {}

        _log(f"  发现 {len(screenshots)} 张截图")

        # 尝试用 Ollama 视觉模型提取元素位置
        try:
            import zhixin
            import executor
            # 取最近的截图（最多5张）
            recent = sorted(screenshots, key=os.path.getmtime, reverse=True)[:5]

            all_elements = {}
            for img_path in recent:
                try:
                    # 直接调用视觉分析
                    config = zhixin._load_config()
                    prompt = (
                        "分析这个屏幕截图，识别所有可点击的UI元素（按钮、图标、菜单项、输入框等），"
                        "估算每个元素的像素坐标和边界框。屏幕分辨率约1920x1080。"
                        "只返回JSON数组：[{\"name\":\"元素名\",\"center\":[x,y],\"bbox\":[x1,y1,x2,y2],\"conf\":0.9}]"
                    )
                    response = zhixin._call_ollama_vision(img_path, prompt, config)
                    # 解析响应
                    import re
                    response = response.strip()
                    if response.startswith("```"):
                        lines = response.split("\n")
                        response = "\n".join(lines[1:]) if len(lines) > 1 else response
                        if response.endswith("```"):
                            response = response[:-3]
                    try:
                        elements = json.loads(response)
                    except:
                        m = re.search(r'\[.*\]', response, re.DOTALL)
                        if m:
                            elements = json.loads(m.group())
                        else:
                            continue

                    if isinstance(elements, list):
                        for el in elements:
                            name = el.get("name", "").strip()
                            if not name:
                                continue
                            if name not in all_elements:
                                all_elements[name] = {
                                    "bbox": el.get("bbox", []),
                                    "center": el.get("center", []),
                                    "confidence": el.get("conf", 0.5),
                                    "learn_count": 1,
                                    "first_seen": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S")
                                }
                            else:
                                # 更新已有元素（平均位置）
                                old = all_elements[name]
                                if el.get("center"):
                                    old_c = old.get("center", [0, 0])
                                    new_c = el["center"]
                                    old["center"] = [
                                        (old_c[0] * old["learn_count"] + new_c[0]) / (old["learn_count"] + 1),
                                        (old_c[1] * old["learn_count"] + new_c[1]) / (old["learn_count"] + 1)
                                    ]
                                old["learn_count"] += 1
                                old["confidence"] = max(old.get("confidence", 0), el.get("conf", 0.5))
                                old["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                except Exception as e:
                    _log(f"  分析截图失败 {os.path.basename(img_path)}: {e}")
                    continue

            # 合并到知识库
            kb = self._load_knowledge()
            for name, info in all_elements.items():
                kb["elements"][name] = info
            self._save_knowledge(kb)

            _log(f"  ✅ 学习完成 — 新增/更新 {len(all_elements)} 个元素")
            return all_elements

        except ImportError:
            _log("  ⚠ zhixin 模块未就绪，跳过学习")
            return {}
        except Exception as e:
            _log(f"  ❌ 学习失败: {e}")
            return {}

    def review(self) -> bool:
        """
        复盘：重新扫描当前屏幕，对比 knowledge 中的位置
        不匹配 → 重新学一次 → 再失败就停止
        """
        _log("🔍 开始复盘验证...")

        kb = self._load_knowledge()
        elements = kb.get("elements", {})

        if not elements:
            _log("  知识库为空，跳过复查")
            return True

        # 截取当前屏幕
        try:
            import executor
            img_path = executor.screenshot()
            if not img_path:
                _log("  截屏失败，跳过复查")
                return True

            # 用视觉模型验证
            import zhixin
            import executor
            config = zhixin._load_config()
            e_names = list(elements.keys())

            prompt = (
                f"请确认以下UI元素是否存在于当前屏幕截图中，并返回它们当前的实际位置：\n"
                + "\n".join(f"- {n}" for n in e_names[:15]) +
                "\n\n返回JSON对象：{\"元素名\":{\"exists\":true/false,\"center\":[x,y],\"moved\":true/false}}"
            )

            response = zhixin._call_ollama_vision(img_path, prompt, config)
            import re
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:]) if len(lines) > 1 else response
                if response.endswith("```"):
                    response = response[:-3]

            try:
                verification = json.loads(response)
            except:
                m = re.search(r'\{.*\}', response, re.DOTALL)
                if m:
                    verification = json.loads(m.group())
                else:
                    _log("  无法解析视觉验证结果")
                    return False

            # 检查不匹配
            mismatches = []
            for name, info in verification.items():
                if isinstance(info, dict) and (info.get("moved") or not info.get("exists")):
                    mismatches.append(name)

            if mismatches:
                _log(f"  ⚠ {len(mismatches)} 个元素位置已变化: {mismatches}")
                # 重新学习一次
                _log("  🔄 触发重新学习...")
                learned = self.learn()
                if not learned:
                    _log("  ❌ 重新学习失败，停止（不再重试）")
                    return False
                _log("  ✅ 重新学习成功")
                return True
            else:
                _log(f"  ✅ 复查通过 — {len(elements)} 个元素位置正确")
                return True

        except ImportError:
            _log("  ⚠ 模块未就绪，跳过复查")
            return True
        except Exception as e:
            _log(f"  ❌ 复查异常: {e}")
            # 重试一次
            _log("  🔄 重试复查...")
            try:
                return self.review()
            except:
                _log("  ❌ 复查重试也失败，停止")
                return False

    def cleanup(self):
        """删除已处理的截图数据，保留 knowledge"""
        _log("🧹 开始清理截图...")

        count = 0
        for root, dirs, files in os.walk(SCREENSHOTS_DIR):
            if "_archived" in root:
                continue
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    src = os.path.join(root, f)
                    try:
                        # 移到归档目录
                        dst = os.path.join(ARCHIVE_DIR, f)
                        # 避免重名
                        if os.path.exists(dst):
                            base, ext = os.path.splitext(f)
                            dst = os.path.join(ARCHIVE_DIR, f"{base}_{int(time.time())}{ext}")
                        shutil.move(src, dst)
                        count += 1
                    except Exception as e:
                        _log(f"  清理失败 {f}: {e}")

        # 删除空子目录
        for root, dirs, files in os.walk(SCREENSHOTS_DIR, topdown=False):
            if "_archived" in root or root == SCREENSHOTS_DIR:
                continue
            try:
                if not os.listdir(root):
                    os.rmdir(root)
            except:
                pass

        # 清理归档中超过7天的旧截图
        cutoff = time.time() - 7 * 86400
        archived = 0
        if os.path.exists(ARCHIVE_DIR):
            for f in os.listdir(ARCHIVE_DIR):
                fp = os.path.join(ARCHIVE_DIR, f)
                try:
                    if os.path.getmtime(fp) < cutoff:
                        os.remove(fp)
                        archived += 1
                except:
                    pass

        _log(f"  ✅ 清理完成 — 归档 {count} 张截图，删除 {archived} 张过期截图")


# 全局单例
_instance = None


def get_instance() -> WenGu:
    global _instance
    if _instance is None:
        _instance = WenGu()
    return _instance
