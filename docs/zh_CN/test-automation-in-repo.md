# 测试自动化资产入仓约定

> T1/T2 用例正文在 **Confluence**；可执行自动化入 **Git**。**路径不猜**——读目标仓库根目录 **`MULTICA.md`**（分仓则读 Issue 矩阵中 **每个相关 repo** 各一份）。

模板：[`templates/zh_CN/MULTICA.md`](../templates/zh_CN/MULTICA.md)（复制到产品仓库根目录）。

---

## 0. 路径解析（强制）

| 场景 | Tester / T3 怎么做 |
| --- | --- |
| **同仓** | 读该 repo 的 MULTICA.md §2 — 须含 UI e2e、API manifest、单测命令 |
| **前后端分仓** | Issue 矩阵列出 frontend repo + backend repo → **分别 Read MULTICA.md**；UI 路径只在前端仓，manifest/单测以后端仓为准（除非前端仓 MULTICA 写明另有 manifest） |
| **MULTICA.md 缺失** | **BLOCKED**，请人类/DevOps 按模板补全后再写自动化 |
| **路径与 skill 默认不一致** | **以 MULTICA.md 为准**（skill 里 `tests/e2e/` 仅为推荐默认值） |

---

## 1. 分工

| 资产 | 主存储 | Git（路径见 MULTICA.md） |
| --- | --- | --- |
| T1/T2 **功能用例正文** | Confluence | 可选 `docs/test/<ISSUE-KEY>/` 草稿 |
| **JIRA** | JIRA | 👤 口令后 XMind → import |
| **接口自动化** | Apifox AI 分支 | `tests/api/<ISSUE-KEY>/manifest.json`（或 MULTICA 指定路径） |
| **UI 自动化** | Git Playwright | MULTICA §2 `UI E2E` 路径（通常 `tests/e2e/`） |

---

## 2. 目录示例（同仓 · 须在 MULTICA.md 中写死）

```text
<product-repo>/
├── MULTICA.md                 # 路径事实来源
├── tests/
│   ├── e2e/                   # Playwright（MULTICA §2）
│   └── api/<ISSUE-KEY>/manifest.json
└── docs/test/<ISSUE-KEY>/     # 可选草稿
```

分仓时：前端仓通常只有 `tests/e2e/`；后端仓通常有 `tests/api/` + 单元测试。

---

## 3. 阶段与入仓时机

| 阶段 | Confluence | Apifox | Git（路径 = MULTICA.md） |
| --- | --- | --- | --- |
| **T1** | 全文 t1-cases；不 XMind | 契约后补场景 | 可选 manifest 占位 |
| **T2** | 增量 t2-coverage | 按清单补场景 | e2e 骨架 + manifest → commit |
| **T3** | 报告贴评论 | run_apifox | deploy 环境跑 MULTICA 中 e2e 命令；修则 commit |

---

## 4. manifest.json 示例

见 [`multica-test-orchestration/references/automation-assets-lifecycle.md`](../templates/zh_CN/skills/multica-test-orchestration/references/automation-assets-lifecycle.md)。

---

## 5. 与门禁

- **G2**：Leader `multica-verification` 对照 AC + 单测证据（可引用 CI，见 gates-and-evidence.md）
- **G3**：T3 跑 MULTICA 中 **e2e** + Apifox；专业把关用 **TestReviewer**（reviewed 版）

---

## 6. 常见错误

| Bad | Better |
| --- | --- |
| 硬编码 `tests/e2e/` 不读 MULTICA | 先 Read 各 repo MULTICA.md §2 |
| 分仓只读一个 MULTICA | 矩阵中每个 repo 各读一份 |
| 路径只写在 Issue 评论 | 写入 MULTICA.md 可持续复用 |
