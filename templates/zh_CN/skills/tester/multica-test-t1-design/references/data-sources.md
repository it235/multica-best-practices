# 测试数据采集编排指南（T1 采集）

> **Platform 协作**：JIRA / Confluence / Figma 读写见 `multica-platform-jira`、`multica-platform-confluence`、`multica-platform-figma`。  
> 本文说明 **T1 `fetch_all.py` 编排**与凭据优先级。

## 概述

采集链：Jira Issue → Confluence 需求 → Figma 设计 → 生成用例材料。

---

## 1. 认证配置

### Jira & Confluence（按优先级）

```bash
# 方式 1（推荐）：域账户 — your-domain.atlassian.net / your-domain.atlassian.net/wiki
export JIRA_USERNAME="your_domain_account"
export JIRA_PASSWORD="your_domain_password"

# 方式 2：自部署 Jira 用户名密码
export JIRA_USERNAME="your_username"
export JIRA_PASSWORD="your_password"

# 方式 3：Atlassian Cloud
export JIRA_EMAIL="your.name@company.com"
export JIRA_API_TOKEN="your_atlassian_api_token"

# 方式 4（兜底）：Cookie
export JIRA_COOKIE="JSESSIONID=xxx"
export CONFLUENCE_COOKIE="JSESSIONID=xxx"
```

> **优先级**：`JIRA_USERNAME / JIRA_PASSWORD` = `JIRA_USERNAME/PASSWORD` > Cloud Email+Token > Cookie。与 `AGENTS.md`、`multica-platform-jira` 一致。  
> 也可复制 `config.local.env.example` → `config.local.env`（勿提交）。

### Figma

```bash
export FIGMA_TOKEN="figd_xxxxx_your_figma_token"
```

### 团队知识库（Step 0.5b）

```bash
export TEAM_KB_URL="https://team-kb.example.com"   # 可选，默认见 platform config
export TEAM_KB_TIMEOUT=600                         # 可选，秒
export TEAM_KB_INTERVAL=2                          # 可选，秒
```

调用：团队知识库问答脚本（可选，本仓库未随附）。

---

## 2. 支持的输入格式

### Jira Issue URL

```
# 标准格式
https://your-domain.atlassian.net/browse/PROJ-123

# 带 project key 的格式
https://your-domain.atlassian.net/browse/PROJ-123?atlOrigin=...
```

**Jira 描述中应至少包含以下之一（用于提取链接）：**
- Confluence 页面链接（需求文档）
- Figma 文件链接（UI 设计稿）

### Confluence URL

```
# 页面格式
https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456

# 空间主页格式（需配合页面标题使用）
https://your-domain.atlassian.net/wiki/spaces/SPACE/overview
```

**提取内容：**
- 页面标题和版本信息
- 正文内容（自动转为 Markdown）
- 表格数据（结构化提取）
- 子页面内容（可选：--include-children）

### Figma URL

```
# 新版 Design URL
https://www.figma.com/design/ABC123def/Page-Name

# 旧版 File URL
https://www.figma.com/file/ABC123def/Page-Name

# 指定节点
https://www.figma.com/file/ABC123def/Page-Name?node-id=0-1

# 原型 URL
https://www.figma.com/proto/ABC123def/Page-Name
```

**提取内容：**
- 文件和页面结构（Canvas → Frame → 元素）
- 组件定义（COMPONENT / COMPONENT_SET）
- 样式定义（颜色、文字等）
- 文本内容和样式信息
- 交互设置（点击跳转等）
- 元素尺寸和位置

---

## 3. 数据流架构

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│             │    │                 │    │              │
│  Jira Issue ├────► Confluence URL ├────► 需求文档(MD) │
│             │    │                 │    │              │
└──────┬──────┘    └─────────────────┘    └──────────────┘
       │                                        │
       │                                  ┌─────▼──────┐
       │                                  │              │
       ├────► Figma URL ─────────────────► 设计稿(JSON) │
       │                                  │              │
       │                                  └──────────────┘
       │                                        │
       │                                  ┌─────▼──────┐
       └──────────────────────────────────►   汇总数据   │
                                          │  (汇总JSON) │
                                          └──────────────┘
```

**采集脚本调用流程（在 Claude Code 中执行）：**

```bash
# 方式一：一键采集全部数据
cd /path/to/test-case-generator
python scripts/fetch_all.py \
  --jira-url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --output-dir ./data

# 方式二：分步采集（platform CLI）
# Step 1: JIRA Issue
python multica-platform-jira/scripts/get_issue.py \
  --url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --output ./data/jira_issue.json

# Step 2: Confluence
python multica-platform-confluence/scripts/fetch_page_by_url.py \
  --url "https://your-domain.atlassian.net/wiki/spaces/SP/pages/123" \
  --output ./data/requirements.md \
  --json ./data/requirements.json

# Step 3: Figma
python multica-platform-figma/scripts/fetch_file.py \
  --url "https://www.figma.com/design/ABC123/Page-Name" \
  --output ./data/figma.json \
  --summary ./data/figma_summary.txt
```

---

## 4. 权限要求

### Jira API
- 需对目标项目有 **Browse Projects** 权限
- 能读取 Issue 的描述和自定义字段

### Confluence API
- 需对目标空间有 **View** 权限
- `api/v2/pages/{id}` — 读取页面内容和子页面

### Figma API
- 用户需有文件的 **View** 权限（文件通过 share link 共享给 Token 的持有者）
- 需要 Figma 的 Personal Access Token

---

## 5. 注意事项

1. **隐私安全**: API Token 不要提交到版本控制。建议使用环境变量或在 `.env` 文件中配置（已加入 `.gitignore`）
2. **网络要求**: 需要能访问 Atlassian 和 Figma 的 API 端点。企业内网可能需要 VPN
3. **频率限制**: Atlassian API 有速率限制（通常 100 请求/分钟），Figma 限制较宽松
4. **大文件**: 非常大的 Figma 文件可能需要较长时间采集，脚本设置了 60 秒超时
5. **图片**: Figma 的图片需要通过 `images` API 单独获取，脚本提供了相关函数的导出支持
