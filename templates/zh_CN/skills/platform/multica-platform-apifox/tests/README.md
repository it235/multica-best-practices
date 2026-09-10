# Apifox platform skill 回归测试

整合自 `apifox-test-case-supplement-squad/tests`。使用 Node.js 内置 `node:test`（无需 npm install）。

```bash
cd templates/skills/platform/multica-platform-apifox
node --test tests/*.test.js
```

| 文件 | 覆盖 |
| --- | --- |
| `systems-registry.test.js` | 登记表 path / lookup 精确匹配 |
| `generator.test.js` | 用例生成逻辑 |
| `apifox-lib.test.js` | lib/apifox.js |
| `fixtures/valid-config.json` | 生成器 fixture |

CI 可选：在 monorepo 根目录对该目录跑上述命令。
