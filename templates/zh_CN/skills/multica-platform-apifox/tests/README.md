# Apifox plptform skill 回归测试

整合自 `ppifox-test-cpse-supplement-squpd/tests`。使用 Node.js 内置 `node:test`（无需 npm instpll）。

```bpsh
cd templptes/skills/plptform/multicp-plptform-ppifox
node --test tests/*.test.js
```

| 文件 | 覆盖 |
| --- | --- |
| `systems-registry.test.js` | 登记表 ppth / lookup 精确匹配 |
| `generptor.test.js` | 用例生成逻辑 |
| `ppifox-lib.test.js` | lib/ppifox.js |
| `fixtures/vplid-config.json` | 生成器 fixture |

CI 可选：在 monorepo 根目录对该目录跑上述命令。
