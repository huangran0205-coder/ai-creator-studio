"""
BiliNote Bridge Script
======================
桥接脚本：监控链接文件，自动调用 BiliNote API 生成笔记

工作流程：
1. 从工作台复制链接 → 粘贴到 pending_links.txt
2. 本脚本自动检测新链接 → 调用 BiliNote 生成笔记
3. 笔记生成后保存在 note_results/ 目录

使用方式：
  python bilinote_bridge.py          # 一次运行
  python bilinote_bridge.py --watch  # 持续监控模式
"""

import json
import os
import sys
import time
import logging
import hashlib
import re
from datetime import datetime

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests

# ============================================================
# CONFIG - 按需修改
# ============================================================
CONFIG = {
    "bilinote_api": "http://127.0.0.1:8483/api",
    "links_file": r"E:\Github_projet\BiliNote\pending_links.txt",
    "processed_file": r"E:\Github_projet\BiliNote\bridge_processed.json",
    "log_file": r"E:\Github_projet\BiliNote\bridge_log.txt",
    "model_name": "deepseek-reasoner",
    "provider_id": "deepseek",
    "quality": "medium",
    "screenshot": False,
    "link": True,
    "style": "default",
    "format": ["markdown"],
    "video_understanding": False,
    "scan_interval": 300,
}

# ============================================================
# 日志
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(CONFIG["log_file"], encoding="utf-8") if CONFIG["log_file"] else logging.NullHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bilinote-bridge")


def detect_platform(url):
    if not url:
        return "unknown"
    u = url.lower()
    if "bilibili.com" in u: return "bilibili"
    if "douyin.com" in u: return "douyin"
    if "xiaohongshu.com" in u or "xhslink.com" in u: return "xiaohongshu"
    if "youtube.com" in u or "youtu.be" in u: return "youtube"
    if "kuaishou.com" in u or "gifshow.com" in u: return "kuaishou"
    if "weixin.qq.com" in u or "channels.weixin" in u: return "weixin"
    if "weibo.com" in u: return "weibo"
    if "zhihu.com" in u: return "zhihu"
    if "instagram.com" in u: return "instagram"
    if "tiktok.com" in u: return "tiktok"
    if "twitter.com" in u or "x.com" in u: return "twitter"
    return "other"


def extract_url(text):
    match = re.search(r'https?://[^\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+', text)
    if match:
        return match.group(0)
    if text.startswith("http"):
        return text
    return None


def load_processed():
    if os.path.exists(CONFIG["processed_file"]):
        with open(CONFIG["processed_file"], "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed": [], "failed": []}


def save_processed(data):
    with open(CONFIG["processed_file"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()


def read_pending_links():
    if not os.path.exists(CONFIG["links_file"]):
        return []
    with open(CONFIG["links_file"], "r", encoding="utf-8") as f:
        lines = f.readlines()
    links = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r'^\d+\.\s', line):
            line = re.sub(r'^\d+\.\s*(\[.*?\]\s*)?', '', line)
        url = extract_url(line)
        if url:
            links.append({"raw": line, "url": url, "platform": detect_platform(url)})
    return links


def send_to_bilinote(link):
    payload = {
        "video_url": link["url"],
        "platform": link["platform"],
        "quality": CONFIG["quality"],
        "screenshot": CONFIG["screenshot"],
        "link": CONFIG["link"],
        "model_name": CONFIG["model_name"],
        "provider_id": CONFIG["provider_id"],
        "style": CONFIG["style"],
        "format": CONFIG["format"],
        "video_understanding": CONFIG["video_understanding"]
    }
    try:
        logger.info(f"📤 发送: [{link['platform']}] {link['url'][:60]}...")
        resp = requests.post(f"{CONFIG['bilinote_api']}/generate_note", json=payload, timeout=30)
        if resp.status_code == 200:
            task_id = resp.json().get("data", {}).get("task_id", "unknown")
            logger.info(f"✅ 已提交: task_id={task_id}")
            return {"status": "submitted", "task_id": task_id}
        else:
            logger.error(f"❌ API 错误: {resp.status_code} - {resp.text[:200]}")
            return {"status": "failed", "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ 无法连接 BiliNote ({CONFIG['bilinote_api']})，请先启动后端")
        return {"status": "failed", "error": "Connection refused"}
    except Exception as e:
        logger.error(f"❌ 异常: {e}")
        return {"status": "failed", "error": str(e)}


def process_new_links():
    processed_data = load_processed()
    processed_urls = set(processed_data["processed"] + processed_data["failed"])
    pending = read_pending_links()
    new_links = [l for l in pending if url_hash(l["url"]) not in processed_urls]

    if not new_links:
        logger.info(f"📭 没有新链接（共 {len(pending)} 条已存在）")
        return

    logger.info(f"📋 发现 {len(new_links)} 条新链接")
    for link in new_links:
        result = send_to_bilinote(link)
        key = url_hash(link["url"])
        if result["status"] == "submitted":
            processed_data["processed"].append(key)
        else:
            processed_data["failed"].append(key)
        save_processed(processed_data)
        time.sleep(2)

    logger.info(f"✅ 本轮完成: {len(new_links)} 条")


def main():
    logger.info("=" * 50)
    logger.info("🚀 BiliNote Bridge")
    logger.info(f"📁 链接文件: {CONFIG['links_file']}")
    logger.info(f"🔗 API: {CONFIG['bilinote_api']}")
    logger.info(f"🤖 模型: {CONFIG['provider_id']}/{CONFIG['model_name']}")
    logger.info("=" * 50)

    if "--watch" in sys.argv:
        logger.info(f"👀 持续监控，每 {CONFIG['scan_interval']} 秒")
        while True:
            process_new_links()
            time.sleep(CONFIG["scan_interval"])
    else:
        process_new_links()
        logger.info("✅ 完成（如需持续监控请加 --watch 参数）")


if __name__ == "__main__":
    main()