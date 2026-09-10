# multica API 参考

来源：multica 服务端路由与 handler 实现（见 multica 源码仓库）。
线上地址：`<MULTICA_API_URL>`（内网部署时通过 `MULTICA_API_URL` 覆盖）。

## 通用约定

- 认证：`Authorization: Bearer <token>`，token 为 Personal Access Token（`mul_` 前缀），在 UI Settings → Access Tokens 创建。注意：本 skill 的脚本不读本地配置文件，token/地址仅来自 `--token`/`--url` 参数或环境变量 `MULTICA_API_TOKEN`/`MULTICA_API_URL`。
- workspace 作用域：请求头 `X-Workspace-Slug: <slug 或 UUID>`，服务端两种都能解析（见 `middleware/auth.go` 的 `resolveWorkspaceID`）。
- CSRF：仅 cookie 会话方式的“状态变更”请求需要 `X-CSRF-Token`；Bearer token 调 GET 无需 CSRF。
- 客户端头（可选，前端会带）：`X-Client-OS: windows`、`X-Client-Platform: web`、`X-Client-Version: dev`、`X-Request-ID: <uuid>`。

## 端点

### 用户级（无需 workspace 头）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/me` | 当前用户信息（id、email、name 等） |

### 需要 `X-Workspace-Slug` 头

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/workspaces` | 当前用户可见的所有 workspace（注意：此接口为全局列表，无需 slug 头） |
| GET | `/api/agents` | workspace 内 agent 列表 |
| GET | `/api/agent-run-counts` | 每个 agent 的 30 天运行次数（Agents 列表 RUNS 列） |
| GET | `/api/agent-activity-30d` | 每个 agent 的 30 天日活（Agents 列表 ACTIVITY 迷你图数据源） |

## 响应结构（源码确认）

### `GET /api/workspaces` → `WorkspaceResponse[]`

```json
[{
  "id": "uuid",
  "name": "My Workspace",
  "slug": "1",
  "description": null,
  "context": null,
  "settings": {},
  "repos": {},
  "issue_prefix": "MYT",
  "avatar_url": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}]
```

### `GET /api/agents` → `AgentResponse[]`

```json
[{
  "id": "uuid",
  "workspace_id": "uuid",
  "runtime_id": "uuid",
  "name": "support-agent",
  "description": "...",
  "instructions": "...",
  "runtime_mode": "issue | autopilot | chat",
  "custom_args": [],
  "archived_at": null,
  "created_at": "...",
  "updated_at": "..."
}]
```

### `GET /api/agent-run-counts` → `AgentRunCount[]`

```json
[{"agent_id": "uuid", "run_count": 20}]
```

### `GET /api/agent-activity-30d` → `AgentActivityBucket[]`

```json
[{"agent_id": "uuid", "bucket_at": "2026-08-23T00:00:00Z", "task_count": 5, "failed_count": 1}]
```

`bucket_at` 为 UTC 当日 0 点，按天聚合。

## 常见错误

| 状态码 | 含义 | 处理 |
| --- | --- | --- |
| 401 | 未认证/token 无效 | 换 token（`--token` 参数或 `MULTICA_API_TOKEN` 环境变量） |
| 403 | 权限不足 / 非 workspace 成员 | 确认 token 所属用户在该 workspace |
| 404 | workspace 不存在 | 用 `workspaces` 子命令确认 slug |
| 502/504 | 服务未就绪 | 检查服务状态（nginx 反代 80 → 后端） |

