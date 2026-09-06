---
name: multica-platform-figma
description: Figma 读：从文件 URL 拉取页面/画板/组件/样式元数据与设计摘要。平台 skill，供 Tester T1、Designer 下游消费。
metadata:
  credentials:
    required:
      - FIGMA_TOKEN
---

# Platform · Figma

## Platform 协作

本 skill 为 **platform 层**；供 `multica-test-t1-design`（fetch_all）、`multica-artifact-ui-sync`、前端 impl 等按名调用。凭据：`FIGMA_TOKEN`。

## Purpose

Figma **读**能力：从 Issue / 设计链接解析 file key，输出结构化 JSON + 可读文本摘要，供测试设计（UI 测试点）与前端实现引用。

> **跨平台**：`python scripts/fetch_file.py`（Windows / macOS / Linux）。

## Files

```text
multica-platform-figma/
├── SKILL.md
├── .env.example
└── scripts/
    ├── fetch_file.py
    └── requirements.txt
```

## Read

```bash
pip install -r scripts/requirements.txt

python scripts/fetch_file.py --url "https://www.figma.com/design/<KEY>/..." \
  --output data/figma.json \
  --summary data/figma_summary.txt
```

| 参数 | 作用 |
| --- | --- |
| `--url` | Figma file / design / proto URL（必填） |
| `--output` / `-o` | 完整 JSON |
| `--summary` / `-s` | 文本摘要（Agent 可直接读） |

凭据：`FIGMA_TOKEN`（Figma → Settings → Personal Access Tokens）。勿写入 Agent Instructions。

## 与产物 / 阶段 skill 的关系

| 调用方 | 实际调用 |
| --- | --- |
| `multica-test-t1-design` | `fetch_all.py` 编排 → 本 skill `fetch_file.py` |
| `multica-artifact-ui-sync` | Designer 产出链接；下游通过本 skill 或 Figma UI 读取 |

完整矩阵见 [`docs/platform-collaboration.md`](../../../../docs/platform-collaboration.md)。

## 为什么有效

Figma REST 与凭据集中在 platform skill；T1 / Designer 只声明「读设计」，不重复 API 细节。
