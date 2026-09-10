# Changelog（Apifox 接口场景补充）

> 整合自 `apifox-test-case-supplement-squad` 版本历史；platform skill 脚本行为以此为准。

## 1.4.9

- 多人多项目：任务卡片、登记表路径可配置、按 OPERATOR 隔离
- Skill 分发空登记模板；运行态/私有文件 gitignore
- config.example 全占位；禁止照搬真实项目 ID
- AI 分支按操作者复用；跨人冲突先问；场景 import 前并发检查
- MULTICA 可复制指令（无本机绝对路径）

## 1.4.8

- 项目 ID 禁止写死示例清单；仅用户输入/登记精确命中/唯一按名
- systems-registry lookup 取消模糊 includes

## 1.4.7

- 同一接口只挂一个场景（WS-40）；断言质量约束
