"""
BiliNote 启动器 — 解决 Windows GBK 编码问题
直接运行此脚本即可启动 BiliNote 后端
"""
import os, sys, subprocess, time, urllib.request, signal, atexit

BACKEND_DIR = r"E:\Github_projet\BiliNote\backend"
PYTHON = r"E:\Github_projet\BiliNote\backend\conda_env\python.exe"
MAIN = r"E:\Github_projet\BiliNote\backend\main.py"
PORT = 8483

def main():
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # 启动 BiliNote
    proc = subprocess.Popen(
        [PYTHON, MAIN],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print(f"✅ BiliNote 已启动 (PID: {proc.pid})")

    # 等待端口可用
    for i in range(30):
        time.sleep(2)
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/sys_health", timeout=2)
            print(f"✅ API 就绪: http://127.0.0.1:{PORT}")
            return proc.pid
        except:
            continue

    print("❌ 启动超时")
    return None

if __name__ == "__main__":
    main()