# AI Creator Studio — 自媒体创作者工作台

> 一个面向双语内容创作者的 PWA 工作台，集成链接收集、AI 灵感讨论、创作管理和笔记导出。

## 项目概述

AI Creator Studio 是一个纯前端单页应用（PWA），服务于自媒体内容创作的全流程：

1. **收集** — 通过油猴脚本、剪贴板检测或手动粘贴，将视频/文章链接收集到收集箱
2. **灵感** — 在灵感库与大模型对话，brainstorm 内容创意，保存讨论历史
3. **创作** — 在创作台撰写和管理工作流（如双语标注项目）
4. **导出** — 将收集箱链接通过 BiliNote 桥接生成 Markdown 笔记，或导出灵感讨论到 Obsidian

## 流程说明

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│  收集链接     │ →  │  灵感库 (AI 对话)│ →  │  创作台       │ →  │  导出笔记/日记   │
│  收集箱       │    │  brainstorm     │    │  工作流管理   │    │  BiliNote /    │
│  (inbox)     │    │  历史讨论        │    │  多阶段任务   │    │  Obsidian      │
└──────────────┘    └─────────────────┘    └──────────────┘    └────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  桥接脚本 bilinote_bridge.py                    │
│  pending_links.txt → BiliNote API → Markdown    │
│  → 存入 Obsidian Vault (F:\OB_vault\note_results) │
└─────────────────────────────────────────────────┘
```

### 完整链路

1. 打开工作台，在收集箱粘贴或检测剪贴板中的链接
2. 点击"导出到 BiliNote"，复制链接内容
3. 粘贴到 `E:\Github_projet\BiliNote\pending_links.txt`
4. 运行桥接脚本，自动调用 BiliNote API 生成笔记
5. 笔记 Markdown 文件保存到 Obsidian vault

## 技术架构

| 层 | 说明 |
|---|---|
| **前端** | 纯静态 PWA：`index.html` + `manifest.json` + `sw.js`，数据存 `localStorage` |
| **油猴脚本** | `collector.user.js`，在各大平台一键收集链接 |
| **桥接脚本** | `bilinote_bridge.py`，连接工作台与 BiliNote 后端 API |
| **后端** | BiliNote Python 服务（独立仓库），端口 `8483` |
| **数据** | 工作台 → `localStorage`（key: `aiStudioInbox`）；BiliNote → SQLite（`bili_note.db`） |
| **笔记输出** | `F:\OB_vault\note_results\`（Obsidian vault） |

## 目录结构

```
ai-creator-studio/
├── index.html              # 主工作台页面（6 个 Tab：工作台/灵感库/创作台/作品集/收集箱/素材库）
├── share-receiver.html     # 分享接收落地页（支持外部链接分享打开）
├── manifest.json           # PWA manifest
├── sw.js                   # Service Worker
├── collector.user.js       # 油猴脚本（各平台一键收集链接）
├── bilinote_bridge.py      # BiliNote 桥接脚本（核心链路）
├── start_bilinote.py       # 桥接脚本启动器
├── install_bridge_task.bat # Windows 定时任务安装脚本
├── README.md               # 本文件
├── .gitignore
└── icons/
    ├── icon-192.svg
    └── icon-512.svg
```

### 关键 localStorage key

| key | 说明 |
|---|---|
| `aiStudioInbox` | 收集箱数据（链接列表、标题、平台、时间戳） |

### 关键外部路径

| 路径 | 说明 |
|---|---|
| `E:\Github_projet\BiliNote\pending_links.txt` | 待处理的链接文件 |
| `E:\Github_projet\BiliNote\bili_note.db` | BiliNote SQLite 数据库 |
| `E:\Github_projet\BiliNote\bridge_processed.json` | 桥接脚本处理记录 |
| `F:\OB_vault\note_results\` | 生成的 Markdown 笔记输出目录 |

## 给其他 Agent 的指导

### 修改范围

| 文件 | 可改 | 说明 |
|---|---|---|
| `index.html` | ✅ 自由修改 | 所有前端 UI/JS 都在这一个文件里 |
| `bilinote_bridge.py` | ✅ 自由修改 | CONFIG 字典配置模型、路径、标签 |
| `collector.user.js` | ✅ 自由修改 | 油猴脚本逻辑 |
| `BiliNote 后端` | ⚠️ 谨慎修改 | 在 `E:\Github_projet\BiliNote\backend\` 下，需重启后端生效 |
| `.gitignore` | ✅ 自由修改 | |

### API 地址

| 端点 | 说明 |
|---|---|
| `http://127.0.0.1:8483/api/generate_note` | 提交链接生成笔记（POST） |
| `http://127.0.0.1:8483/api/task_status/{task_id}` | 查询任务状态（GET） |
| `http://127.0.0.1:8483/api/get_all_providers` | 获取 provider 列表（GET） |
| `http://127.0.0.1:8483/api/add_provider` | 添加 provider（POST） |
| `http://127.0.0.1:8483/api/models` | 注册模型（POST） |

### 桥接脚本 CONFIG 关键配置

```python
CONFIG = {
    "bilinote_api": "http://127.0.0.1:8483/api",
    "model_name": "sensenova-6.7-flash-lite",
    "provider_id": "<UUID>",           # SenseNova provider 的 UUID
    "links_file": r"E:\Github_projet\BiliNote\pending_links.txt",
    "obsidian_dir": r"F:\OB_vault\note_results",
    "platform_tags": { ... },          # 平台 → 标签映射
    "global_tags": ["#collected"],     # 全局标签
}
```

### 注意事项

- 前端是纯静态，**没有任何后端服务器**，所有逻辑在浏览器端运行
- `bilinote_bridge.py` 需要独立的 Python 环境（BiliNote 的 conda env）
- BiliNote 后端需要独立启动，桥接脚本才能工作
- `index.html` 中的 JS 是全局作用域，新增函数注意不冲突

## 使用指南

### 启动

#### 方式 A：浏览器直接打开

```
双击 index.html 或用浏览器打开
```

适合日常使用，PWA 支持添加到桌面/开始菜单。

#### 方式 B：启动 BiliNote 管理前端

```powershell
cd "E:\Github_projet\BiliNote\BillNote_frontend"
pnpm dev
# 访问 http://localhost:3015
```

用于管理 BiliNote 的 provider、模型和查看笔记历史。

#### 方式 C：启动后端

```powershell
cd "E:\Github_projet\BiliNote\backend"
.\conda_env\python.exe main.py
# 监听 http://0.0.0.0:8483
```

### 收集链接

1. **油猴脚本**：安装 `collector.user.js`，在 B站/抖音/YouTube 页面一键收集
2. **剪贴板检测**：在工作台点击"检测剪贴板"按钮，自动识别链接
3. **手动粘贴**：在收集箱输入框粘贴链接，回车添加

### 导出到 BiliNote

1. 在收集箱点击"一键复制全部链接"
2. 粘贴到 `E:\Github_projet\BiliNote\pending_links.txt`
3. 运行桥接脚本：

```powershell
cd "F:\OB_vault\ai-creator-studio"
"E:\Github_projet\BiliNote\backend\conda_env\python.exe" bilinote_bridge.py
```

或持续监控模式：

```powershell
"E:\Github_projet\BiliNote\backend\conda_env\python.exe" bilinote_bridge.py --watch
```

### 桥接脚本配置

编辑 `bilinote_bridge.py` 顶部的 `CONFIG` 字典：

- `model_name` / `provider_id`：选择大模型
- `platform_tags`：自定义平台标签映射
- `global_tags`：全局标签（每个笔记都会带上）
- `obsidian_dir`：Markdown 输出目录

## 开发计划

- [x] 桥接脚本：提交 → 轮询 → 取 Markdown → 写入 Obsidian
- [x] 桥接脚本：提取视频真实标题（非 URL）
- [x] 桥接脚本：平台标签 + 全局标签
- [x] 灵感库：接入大模型 API（通过 BiliNote 后端代理，绕过 CORS）
- [x] 灵感库：历史讨论保存（localStorage）
- [x] 灵感库：话题模板推荐
- [x] 灵感库：从收集箱导入灵感
- [x] 灵感库：导出到 Obsidian
- [ ] 灵感库：GitHub Pages 部署
- [ ] 灵感库：移动端 PWA 适配优化
- [ ] 创作台：工作流状态持久化

---

## 灵感库配置指南

### 原理

灵感库通过 BiliNote 后端做 API 代理，绕过浏览器 CORS 限制：

```
前端 (http://127.0.0.1:5500)
  → POST /api/inspire/chat  （同源，无 CORS 问题）
    → BiliNote 后端转发到 SenseNova API
      → 返回结果给前端
```

### 后端配置（一次性）

在 BiliNote 后端新增代理端点（详见 `INSPIRE_BACKEND_SETUP.md`）：

1. 新建 `E:\Github_projet\BiliNote\backend\app\routers\inspire.py`
2. 在 `app/__init__.py` 的 `create_app()` 中加一行：
   ```python
   from .routers import inspire
   app.include_router(inspire.router, prefix="/api")
   ```
3. 重启 BiliNote 后端

### 前端配置

打开灵感库 → 点击右上角 ⚙️ 配置：

| 字段 | 值 |
|------|------|
| Base URL | `https://token.sensenova.cn/v1` |
| API Key | `sk-capZuTqIBgSquRvnCXDgLBaWGIBggRxw` |
| 模型 | `sensenova-6.7-flash-lite` |

### 验证代理端点

```powershell
curl -X POST "http://127.0.0.1:8483/api/inspire/chat" `
  -H "Content-Type: application/json" `
  -d '{
    "messages": [{"role":"user","content":"hello"}],
    "base_url": "https://token.sensenova.cn/v1",
    "api_key": "sk-capZuTqIBgSquRvnCXDgLBaWGIBggRxw",
    "model": "sensenova-6.7-flash-lite"
  }'
```

返回 `{"content":"...","error":null}` 说明代理端点正常。

---

## 部署指南

### 方案 A：GitHub Pages（推荐）

适合手机随时访问，不需要同 WiFi。

```powershell
# 1. 推代码到 GitHub
cd "F:\OB_vault\ai-creator-studio"
git push origin main

# 2. 在 GitHub 仓库 Settings → Pages
#    Source: Deploy from a branch
#    Branch: main / (root)
#    保存后访问 https://<username>.github.io/ai-creator-studio/
```

**注意**：GitHub Pages 是静态托管，需要 BiliNote 后端在本地一直运行（8483 端口），灵感库才能对话。

### 方案 B：本地 HTTP 服务

```powershell
# 双击 start_frontend.bat 或运行：
cd "F:\OB_vault\ai-creator-studio"
python -m http.server 8000
# 访问 http://localhost:8000
```

### 方案 C：Live Server（VS Code）

1. 安装 Live Server 扩展
2. 右键 `index.html` → Open with Live Server
3. 访问 `http://127.0.0.1:5500/ai-creator-studio/index.html`
