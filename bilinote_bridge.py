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
    "model_name": "sensenova-6.7-flash-lite",
    "provider_id": "c5bb19b1-7e30-421a-8a4d-b2e3ab81ea58",
    "quality": "medium",
    "screenshot": False,
    "link": True,
    "style": "default",
    "format": ["markdown"],
    "video_understanding": False,
    "scan_interval": 300,
    # 输出到 Obsidian vault 的目录
    "obsidian_dir": r"F:\OB_vault\note_results",
    # 轮询任务状态参数
    "poll_interval": 10,       # 每 N 秒查询一次
    "poll_timeout": 900,       # 最长等待 N 秒（15 分钟）
    "status_success": "SUCCESS",
    "status_failed": "FAILED",
    "status_pending": "PENDING",
    # 平台标签映射：每个平台对应的 Obsidian 标签列表
    "platform_tags": {
        "bilibili":    ["#B站", "#video"],
        "youtube":     ["#YouTube", "#video"],
        "douyin":      ["#抖音", "#video"],
        "kuaishou":    ["#快手", "#video"],
        "weixin":      ["#微信公众号", "#article"],
        "weibo":       ["#微博", "#article"],
        "zhihu":       ["#知乎", "#article"],
        "xiaohongshu": ["#小红书", "#article"],
        "default":     ["#note"],
    },
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
        with open(CONFIG["processed_file"], "r", encoding="utf-8-sig") as f:
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
            resp_json = resp.json() or {}
            code = resp_json.get("code")
            # 后端返回 200 但 code!=0 也是失败
            if code and code != 0:
                msg = resp_json.get("msg", f"code={code}")
                logger.error(f"❌ API 逻辑错误: {msg}")
                return {"status": "failed", "error": msg}
            data = resp_json.get("data") or {}
            task_id = data.get("task_id", "unknown")
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


def poll_task_status(task_id: str):
    """轮询任务状态直到完成或超时，返回 (status, result_or_error)"""
    url = f"{CONFIG['bilinote_api']}/task_status/{task_id}"
    elapsed = 0
    while elapsed < CONFIG["poll_timeout"]:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                logger.error(f"⚠️ 状态查询失败: HTTP {resp.status_code}")
                return "error", resp.text[:200]

            data = resp.json().get("data", {})
            status = data.get("status", "unknown")

            if status == CONFIG["status_success"]:
                result = data.get("result", {})
                logger.info(f"✅ 任务完成 (task_id={task_id})")
                return "success", result

            if status == CONFIG["status_failed"]:
                msg = data.get("message", "unknown")
                logger.error(f"❌ 任务失败: {msg}")
                return "failed", msg

            logger.debug(f"⏳ 任务进行中 [{status}] (task_id={task_id}, elapsed={elapsed}s)")
        except requests.exceptions.ConnectionError:
            logger.error("❌ 无法连接后端查询状态")
            return "error", "Connection refused"
        except Exception as e:
            logger.error(f"❌ 轮询异常: {e}")
            return "error", str(e)

        time.sleep(CONFIG["poll_interval"])
        elapsed += CONFIG["poll_interval"]

    logger.error(f"⏰ 轮询超时 (task_id={task_id}, elapsed={elapsed}s)")
    return "timeout", "Polling timeout"


def save_markdown_to_obsidian(task_id: str, result: dict, link: dict):
    """将生成的 Markdown 保存到 Obsidian vault，带标题和标签"""
    obsidian_dir = CONFIG["obsidian_dir"]
    os.makedirs(obsidian_dir, exist_ok=True)

    # 从 result 里拿 markdown 内容
    markdown = (
        result.get("markdown")
        or result.get("md_content")
        or result.get("content")
        or ""
    )
    if not markdown:
        logger.warning(f"⚠️ 任务 {task_id} 返回结果中无 markdown 内容")
        return None

    # 提取视频真实标题（从 audio_meta.fulltitle 或 audio_meta.title）
    title = ""
    audio_meta = result.get("audio_meta") or {}
    # raw_info 里可能有 fulltitle
    raw_info = audio_meta.get("raw_info") or {}
    title = (
        audio_meta.get("title")
        or raw_info.get("title")
        or raw_info.get("fulltitle")
        or ""
    )
    # 去掉 B 站标题末尾的宣传后缀（用 | 分隔）
    if "|" in title:
        title = title.split("|")[0].strip()
    if not title:
        title = link["raw"][:80]

    # 根据平台打标签
    platform = link["platform"]
    platform_tags = CONFIG.get("platform_tags", {})
    tags = platform_tags.get(platform, platform_tags.get("default", ["#note"]))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建文件名：用任务 ID
    filename = f"{task_id}.md"
    filepath = os.path.join(obsidian_dir, filename)

    # 构建 front matter
    front_matter = (
        f"---\n"
        f"title: {title}\n"
        f"platform: {platform}\n"
        f"url: {link['url']}\n"
        f"tags: [{', '.join(tags)}]\n"
        f"task_id: {task_id}\n"
        f"created: {timestamp}\n"
        f"---\n\n"
    )

    content = front_matter + markdown
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"📝 Markdown 已保存: {filepath}")
    logger.info(f"   标题: {title}")
    logger.info(f"   标签: {', '.join(tags)}")
    logger.info(f"   文件大小: {os.path.getsize(filepath)} bytes")
    return filepath


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
        # Step 1: 提交任务
        submit = send_to_bilinote(link)
        key = url_hash(link["url"])

        if submit["status"] != "submitted":
            logger.error(f"❌ 提交失败: {submit.get('error')}")
            processed_data["failed"].append(key)
            save_processed(processed_data)
            continue

        task_id = submit["task_id"]

        # Step 2: 轮询等待完成
        logger.info(f"⏳ 等待任务完成... (task_id={task_id})")
        status, data = poll_task_status(task_id)

        if status == "success":
            # Step 3: 保存 Markdown 到 Obsidian
            filepath = save_markdown_to_obsidian(task_id, data, link)
            if filepath:
                processed_data["processed"].append(key)
                logger.info(f"✅ [{link['platform']}] 笔记已存入 Obsidian: {filepath}")
            else:
                processed_data["failed"].append(key)
                logger.error(f"❌ 无法保存 Markdown (task_id={task_id})")
        else:
            processed_data["failed"].append(key)
            logger.error(f"❌ [{link['platform']}] 任务异常: {status} - {data}")

        save_processed(processed_data)
        time.sleep(2)

    logger.info(f"✅ 本轮完成: {len(new_links)} 条")


def main():
    logger.info("=" * 50)
    logger.info("🚀 BiliNote Bridge")
    logger.info(f"📁 链接文件: {CONFIG['links_file']}")
    logger.info(f"🔗 API: {CONFIG['bilinote_api']}")
    logger.info(f"🤖 模型: {CONFIG['provider_id']}/{CONFIG['model_name']}")
    logger.info(f"📝 输出目录: {CONFIG['obsidian_dir']}")
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