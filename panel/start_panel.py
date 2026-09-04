#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静物插画面板启动器。
功能：
1. 检测端口8765是否被占用（面板是否已运行）
2. 已运行则直接打开浏览器，不重复启动
3. 未运行则启动本地HTTP服务器（后台），然后打开浏览器
4. 优先在豆包内置浏览器打开，不支持则回退默认浏览器
5. 服务器根目录为技能根目录，面板地址 http://127.0.0.1:8765/panel/panel_pro.html
6. 提供 /api/list-images 端点，扫描指定目录下的 *_final.png 并返回JSON列表
7. 提供 /api/scan-project 端点，自动扫描默认项目目录（递归）

API用法：
  GET /api/list-images?dir=<目录路径URL编码>&recursive=1
    recursive=1 时递归扫描子目录，按修改时间降序，最多50张
  返回：{"images": [{"name": "B001_A_final.png", "size": 12345, "mtime": "2026-09-02 22:00:00", "url": "/api/image?path=..."}], "count": 4}

  GET /api/scan-project
    自动扫描默认项目目录（环境变量 STILL_LIFE_PROJECT_DIR 或默认 C:\\Users\\<user>\\Doubao\\chats\\）
    递归扫描，按修改时间降序，最多50张

用法：
  python start_panel.py
  python start_panel.py --port 8765
  python start_panel.py --no-browser       # 只启动服务器不打开浏览器
  python start_panel.py --browser "C:\\path\\to\\browser.exe"  # 指定浏览器
  python start_panel.py --project-dir "C:\\path\\to\\project"  # 指定默认项目目录
"""
import argparse
import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime

# 技能根目录（start_panel.py 在 panel/ 下，根目录是上一级）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PORT = 8765
PANEL_PATH = "panel/panel_pro.html"
MAX_IMAGES = 50  # 递归扫描时最多返回的图片数量
# 全部图片模式支持的扩展名
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
# 图片扩展名 -> HTTP Content-Type
IMAGE_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def match_image(fname, img_filter="final"):
    """判断文件名是否符合图片范围。
    final：仅成品 *_final.png；all：png/jpg/jpeg/webp/bmp 全部图片（任意路径可扫）。"""
    lower = fname.lower()
    if img_filter == "all":
        return lower.endswith(IMAGE_EXTENSIONS)
    return lower.endswith("_final.png")

# 豆包进程名（Windows）
DOUBAO_PROCESS_NAMES = ["Doubao.exe", "doubao.exe", "豆包.exe"]

# 默认项目目录（可通过环境变量或 --project-dir 覆盖）
def get_default_project_dir():
    """获取默认项目目录。
    优先级：环境变量 STILL_LIFE_PROJECT_DIR > 用户主目录下的 Doubao/chats
    """
    env_dir = os.environ.get("STILL_LIFE_PROJECT_DIR", "")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    # 默认：用户主目录下的 Doubao/chats
    home = os.path.expanduser("~")
    default = os.path.join(home, "Doubao", "chats")
    if os.path.isdir(default):
        return default
    # 回退：用户主目录
    return home


def is_port_in_use(port, host="127.0.0.1"):
    """检测端口是否被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False


def is_doubao_running():
    """检测豆包客户端是否在运行（Windows）。"""
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Doubao.exe"],
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return b"Doubao.exe" in result
    except Exception:
        return False


def scan_final_images(directory, recursive=False, max_count=MAX_IMAGES, img_filter="final"):
    """扫描指定目录下的图片，返回列表（任意目录路径均可，无白名单限制）。
    img_filter="final" 仅成品 *_final.png；img_filter="all" 支持 png/jpg/jpeg/webp/bmp。
    recursive=True 时递归扫描子目录、按修改时间降序；每条带 relpath（相对扫描根，标识来源子目录）。
    """
    if not directory or not os.path.isdir(directory):
        return []
    images = []
    try:
        if recursive:
            # 递归扫描
            for root, dirs, files in os.walk(directory):
                for fname in files:
                    if match_image(fname, img_filter):
                        fpath = os.path.join(root, fname)
                        try:
                            stat = os.stat(fpath)
                            images.append({
                                "name": fname,
                                "path": fpath,
                                "relpath": os.path.relpath(fpath, directory),
                                "size": stat.st_size,
                                "mtime_ts": stat.st_mtime,
                                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                                "url": "/api/image?path=" + urllib.parse.quote(fpath),
                            })
                        except Exception:
                            pass
            # 按修改时间降序排序
            images.sort(key=lambda x: x["mtime_ts"], reverse=True)
            # 限制数量
            images = images[:max_count]
            # 移除内部临时字段（保留 relpath 供前端显示来源子目录）
            for img in images:
                del img["mtime_ts"]
                del img["path"]
        else:
            # 只扫描当前目录
            for fname in sorted(os.listdir(directory)):
                fpath = os.path.join(directory, fname)
                if match_image(fname, img_filter) and os.path.isfile(fpath):
                    stat = os.stat(fpath)
                    images.append({
                        "name": fname,
                        "relpath": fname,
                        "size": stat.st_size,
                        "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "url": "/api/image?path=" + urllib.parse.quote(fpath),
                    })
    except Exception:
        pass
    return images


class PanelHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，支持静态文件服务和API端点。"""

    def _same_origin_guard(self):
        """仅允许本机访问：校验 Host（防 DNS rebinding）与 Origin（防其他网页跨站读取本机文件）。"""
        port = self.server.server_address[1]
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        host = self.headers.get("Host", "")
        if host and host not in allowed_hosts:
            self.send_error(403, "Forbidden host")
            return False
        origin = self.headers.get("Origin", "")
        if origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
            self.send_error(403, "Forbidden origin")
            return False
        return True

    def do_GET(self):
        if not self._same_origin_guard():
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API: 列出指定目录下的 final 图片
        if path == "/api/list-images":
            directory = query.get("dir", [""])[0]
            directory = urllib.parse.unquote(directory)
            recursive = query.get("recursive", ["0"])[0] == "1"
            img_filter = query.get("filter", ["final"])[0]
            if img_filter not in ("final", "all"):
                img_filter = "final"
            images = scan_final_images(directory, recursive=recursive, img_filter=img_filter)
            response = {
                "count": len(images),
                "directory": directory,
                "recursive": recursive,
                "filter": img_filter,
                "images": images,
            }
            self.send_json_response(response)
            return

        # API: 自动扫描默认项目目录（递归）
        if path == "/api/scan-project":
            project_dir = get_default_project_dir()
            images = scan_final_images(project_dir, recursive=True)
            response = {
                "count": len(images),
                "directory": project_dir,
                "recursive": True,
                "images": images,
            }
            self.send_json_response(response)
            return

        # API: 读取指定路径的图片文件
        if path == "/api/image":
            image_path = query.get("path", [""])[0]
            image_path = urllib.parse.unquote(image_path)
            ext = os.path.splitext(image_path)[1].lower()
            if image_path and os.path.isfile(image_path) and ext in IMAGE_CONTENT_TYPES:
                try:
                    with open(image_path, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", IMAGE_CONTENT_TYPES[ext])
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception:
                    pass
            self.send_error(404, "Image not found")
            return

        # 其他请求：静态文件服务
        super().do_GET()

    def send_json_response(self, data):
        """发送JSON响应。"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """静默日志，不输出请求日志。"""
        pass


def start_server(port, root_dir):
    """在后台启动HTTP服务器。"""
    os.chdir(root_dir)
    server = http.server.HTTPServer(("127.0.0.1", port), PanelHTTPRequestHandler)
    server.serve_forever()


def open_browser(port, browser_path=None):
    """打开浏览器访问面板。
    优先级：指定浏览器 > 豆包内置浏览器（如果豆包在运行） > 默认浏览器
    """
    url = f"http://127.0.0.1:{port}/{PANEL_PATH}"

    # 1. 用户指定了浏览器路径
    if browser_path:
        try:
            subprocess.Popen([browser_path, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[面板] 已在指定浏览器打开: {url}")
            return True
        except Exception as e:
            print(f"[面板] 指定浏览器打开失败，尝试其他方式: {e}")

    # 2. 优先尝试豆包内置浏览器（如果豆包在运行）
    if is_doubao_running():
        try:
            # Windows上用os.startfile，如果豆包注册了URL协议会在豆包内置浏览器打开
            if sys.platform == "win32":
                os.startfile(url)
                print(f"[面板] 已尝试在豆包内置浏览器打开: {url}")
                print(f"  提示：如果未在豆包中打开，请手动复制上方URL到豆包内置浏览器地址栏。")
                return True
        except Exception as e:
            print(f"[面板] 豆包内置浏览器打开失败，回退默认浏览器: {e}")

    # 3. 回退到默认浏览器
    try:
        webbrowser.open(url)
        print(f"[面板] 已在默认浏览器打开: {url}")
        return True
    except Exception as e:
        print(f"[面板] 自动打开浏览器失败，请手动访问: {url}")
        print(f"  错误: {e}")
        return False


def main():
    ap = argparse.ArgumentParser(description="静物插画面板启动器")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"端口号（默认 {DEFAULT_PORT}）")
    ap.add_argument("--no-browser", action="store_true", help="只启动服务器，不打开浏览器")
    ap.add_argument("--browser", default=None, help="指定浏览器可执行文件路径")
    ap.add_argument("--project-dir", default=None, help="指定默认项目目录（用于自动扫描）")
    ap.add_argument("--stop", action="store_true", help="停止已运行的面板服务器（仅提示，不强制kill）")
    args = ap.parse_args()

    # 设置默认项目目录
    if args.project_dir:
        os.environ["STILL_LIFE_PROJECT_DIR"] = args.project_dir

    print(f"[面板] 技能根目录: {SKILL_ROOT}")
    print(f"[面板] 端口: {args.port}")
    print(f"[面板] 面板地址: http://127.0.0.1:{args.port}/{PANEL_PATH}")
    print(f"[面板] 默认项目目录: {get_default_project_dir()}")
    print(f"[面板] API: http://127.0.0.1:{args.port}/api/list-images?dir=<目录>&recursive=1")
    print(f"[面板] API: http://127.0.0.1:{args.port}/api/scan-project（自动扫描项目目录）")

    if args.stop:
        if is_port_in_use(args.port):
            print(f"[面板] 端口 {args.port} 已被占用，面板可能正在运行。")
            print(f"  如需停止，请手动关闭对应进程，或重启电脑。")
        else:
            print(f"[面板] 端口 {args.port} 未被占用，面板未运行。")
        return

    # 检测端口
    if is_port_in_use(args.port):
        print(f"[面板] 端口 {args.port} 已被占用，面板正在运行，直接打开浏览器。")
        if not args.no_browser:
            open_browser(args.port, args.browser)
        return

    # 启动服务器（后台线程）
    print(f"[面板] 启动本地HTTP服务器...")
    server_thread = threading.Thread(
        target=start_server,
        args=(args.port, SKILL_ROOT),
        daemon=True
    )
    server_thread.start()

    # 等待服务器启动
    time.sleep(1.0)

    # 验证服务器是否启动成功
    if is_port_in_use(args.port):
        print(f"[面板] 服务器启动成功，运行在 http://127.0.0.1:{args.port}")
        if not args.no_browser:
            open_browser(args.port, args.browser)
        print(f"[面板] 服务器随本进程运行：直接启动时，关闭本窗口或结束进程服务器即停止。")
        print(f"[面板] 如需关窗常驻（豆包 Windows 沙箱），请按 SKILL.md 用计划任务 + _run_panel.vbs 方式启动。")
        # 保持主线程运行，让服务器持续服务
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\n[面板] 已停止。")
    else:
        print(f"[面板] 服务器启动失败，请检查端口 {args.port} 是否被其他程序占用。")
        sys.exit(1)


if __name__ == "__main__":
    main()
