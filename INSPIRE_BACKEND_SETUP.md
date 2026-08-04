# BiliNote 后端 — 新增 Inspire Chat 代理端点

文件：`E:\Github_projet\BiliNote\backend\app\routers\inspire.py`

```python
"""
Inspire Chat Router — 前端 AI 对话 API 代理
"""

import httpx
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    base_url: str
    api_key: str
    model: str


class ChatResponse(BaseModel):
    content: str
    error: str | None = None


@router.post("/inspire/chat")
async def inspire_chat(req: ChatRequest):
    """代理转发到外部大模型 API"""
    target_url = req.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {req.api_key}",
    }
    body = {
        "model": req.model,
        "messages": [
            {"role": m.role, "content": m.content}
            for m in req.messages
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(target_url, json=body, headers=headers)

        if resp.status_code != 200:
            return ChatResponse(content="", error=f"API 返回 {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "(无回复内容)")
        return ChatResponse(content=content)

    except httpx.TimeoutException:
        return ChatResponse(content="", error="请求超时（超过 120 秒）")
    except httpx.ConnectError:
        return ChatResponse(content="", error=f"无法连接到 {target_url}")
    except Exception as e:
        return ChatResponse(content="", error=f"转发异常: {e}")
```

然后在 `app/__init__.py` 中添加：

```python
from .routers import inspire

# 在 create_app() 函数内已有 include_router 下面加：
app.include_router(inspire.router, prefix="/api")
```

---

## 手机方案

你提到手机和电脑不在同一个 WiFi，所以局域网 IP 方案不行。以下是 **不需要同 WiFi 的手机方案**：

| 方案 | 做法 |
|------|------|
| **A. GitHub Pages 部署** | 把前端推到 GitHub 仓库 → GitHub Pages 自动部署 → 手机访问 `https://你的用户名.github.io/ai-creator-studio/`，和电脑共用同一个 URL |
| **B. ngrok 内网穿透** | 电脑上跑 `ngrok http 5500` → 生成公网 URL → 手机访问，无需同 WiFi |
| **C. 把前后端都部署到云端** | 后端跑在云服务器，前端用 GitHub Pages，手机直接访问 |

推荐 **A 方案**——最简单，而且你已经有 GitHub 仓库了（`origin/main`）。

---

### A 方案：GitHub Pages 部署

1. 确保 BiliNote 后端代理端点已加好
2. 把后端 CORS 放开（在 `main.py` 里加 `origins = ["*"]`）
3. 推代码到 GitHub
4. GitHub → Settings → Pages → 选 main 分支 → 保存
5. 访问 `https://你的用户名.github.io/ai-creator-studio/`

这样电脑和手机都用同一个 GitHub Pages URL，无需同 WiFi。

要我帮你做 GitHub Pages 部署的相关改动吗？还是你更倾向 ngrok 方案？
