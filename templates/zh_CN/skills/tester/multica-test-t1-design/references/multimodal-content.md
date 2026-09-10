# 多模态内容处理（HTML + 图片）

> 整合自 `test-case-generator-squad`。采集脚本经 platform skill；Agent 读阶段仍须遵守本规则。

## 目标

不遗漏需求文档中的表格、列表、流程图、UI 截图、数据字典等信息。

## HTML / ADF

从 Jira ADF、Confluence Storage Format 提取：

- **表格**：行列对应、表头含义
- **列表**：顺序与层级
- **格式化**：加粗/高亮关键词
- **代码块 / 宏**：接口示例、配置

**禁止** strip 标签后把表格变成散落文字。

`fetch_all` 汇总 JSON 含 `rich_content`、`confluence_details`；有表格/图片时 stderr 会提示。

### `fetch_all.py` 输出字段（Agent 须读）

汇总文件：`summary_{timestamp}.json`

| 字段 | 说明 |
| --- | --- |
| `jira.key` / `jira.summary` | Issue Key 与标题 |
| `jira.description_text` / `description_html` | Jira 描述（文本 + HTML） |
| `jira.image_attachments[]` | Jira 图片附件（来自 platform `get_issue.py`） |
| `confluence_pages[]` | 关联 Confluence 页面摘要 |
| `confluence_details[]` | 每页：`url`、`title`、`has_rich_content`、`image_count`、`has_tables`、`has_lists`、`has_images` |
| `figma_files[]` | Figma 采集结果 |
| `rich_content.has_rich_content` | 是否存在需多模态处理的内容 |
| `rich_content.total_images` | Confluence 图片引用总数 |
| `rich_content.has_jira_images` | Jira 是否有图片附件 |

stderr 出现「检测到富内容」或图片计数 > 0 时，Agent **必须** Read 图片并处理表格/列表。

## 图片

1. **检测**：Confluence `<ac:image>`、Jira ADF `media`、附件列表、Markdown `![]()`
2. **下载**：platform `fetch_page_by_url.py` 默认 `--image-dir`；Jira 附件见 `get_issue.py` 的 `image_attachments`
3. **读取**：对下载的图片 **必须使用 Read 工具** 视觉识别
4. **文字化**：流程步骤、UI 元素、字段定义、状态机写入需求理解
5. **覆盖报告**：标注「通过图片获取的规则/信息」

## 融合理解

1. **收集**：Jira 文本 + ADF/HTML + Confluence MD + 图片 + Figma
2. **交叉验证**：文字 vs 图片 vs 表格一致性
3. **冲突优先级**：JIRA AC > 当前 Confluence PRD > API > Figma > 历史/知识库
4. **需求点拆分**：每条规则/界面/流程/约束 → 可测试点
5. **覆盖映射**：标记来源（文字/表格/图片/Figma）

## Confluence wiki 标记清理

生成用例前清理 `{LQ}` `{RQ}` `{color}` `{noformat}` 等；不得带入用例正文。

## 阻塞提示

采集完成但有未下载图片引用 → 在 blockers 记录，继续处理已获取内容；关键图片无法读取且影响 AC → 标注阻塞。
