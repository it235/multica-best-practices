# 命名规范：角色 + 项目 + 成员标识

> 目的：同一角色定义可以实例化多个 Agent，靠名字区分、不靠改指令——流程因此可复用。当同一项目里有多个同角色成员（如多名前端），仅「角色 + 项目」仍会冲突，需要再加一段成员标识。

## 规则

1. Agent 名 = `<角色>-<项目>-<成员标识>`，角色取固定词表。
2. 角色词表：`Leader / ProductManager / Architect / Designer / FrontendDev / BackendDev / Tester / Reviewer`
3. `<项目>` = 服务 / 领域 / 项目名称（小写连字符），例如 `user-service`、`web`、`order`。
4. `<成员标识>` = 该成员在「本项目 + 本角色」下的唯一标识，用工号或花名（如 `u1024`、`阿杰`），不要用真实姓名全称（避免 PII，也避免同一人跨项目重名歧义）。
5. 名字只区分实例，不承载职责；职责永远来自 Agent Instructions / Squad Instructions。
6. `Architect` 是技术架构设计（改动方案 / 文件 / 验证），`Designer` 是 UI / 交互设计（设计平台由 `multica-design-ui-impl` skill 决定）；二者专业与产物不同，不要合并。

## 示例

| 角色 | 示例名 | 说明 |
| --- | --- | --- |
| BackendDev | `BackendDev-user-service-u1024` | 用户服务后端（成员工号 u1024）|
| FrontendDev | `FrontendDev-web-阿杰` | Web 前端（成员花名 阿杰）|
| Tester | `Tester-order-lina` | 订单域测试（成员花名 lina）|
| Architect | `Architect-core-u2031` | 核心架构设计（成员工号 u2031）|
| Designer | `Designer-web-mei` | Web UI / 交互设计（设计平台由 skill 决定，花名 mei）|
| Leader | `Leader-core-u0001` | 核心小队 Leader（成员工号 u0001）|

> 三段式解决了「真实姓名 vs 角色名」的冲突：角色名保证可读、可路由；项目段隔离不同服务；成员标识（工号/花名）在「同项目同角色多人」时唯一区分。模板里成员标识用占位符 `<member>`，不写死真名，保持 Copy-Paste-Run。

## 小队实例后缀与前缀通配

Squad Instructions 里用 `@Architect` / `@FrontendDev` 等**角色前缀**指代成员，而非写死完整 Agent 名——这样 `squad.md` 才能原样复制。但一个 workspace 里常驻多个同角色实例（如 `FrontendDev-web-阿杰`、`FrontendDev-web-lina`），指挥必须能锁定「本小队」那一个。规则如下：

1. 每个小队在启动时声明自己的**实例后缀** `suffix`（如 `payment`、`order`），与本小队所有角色绑定；它对应命名里的 `<项目>` 段。
2. Squad Instructions 中凡是写 `@角色` 的地方，指挥一律按 `@角色-<本小队 suffix>-<本小队 member>` 解析后精确 @mention。
   - 例：`suffix = payment`、`member = u1024` 时，`@FrontendDev` → 实际派给 `FrontendDev-payment-u1024`，`@Architect` → `Architect-payment-u1024`。
3. 若某角色不在本小队范围（Issue【范围】不含该层），按既有规则跳过对应产物，不解析、不派活。
4. `suffix` 与 `member` 只在小队配置时设定一次，不写进 `squad.md`；`squad.md` 永远只出现角色前缀，保持可复制。

> 这样「角色前缀」是 Squad 内的逻辑名，「`@角色-项目-成员标识`」是 workspace 内的物理名，二者通过小队配置桥接。

## 为什么

- Multica 里 Agent 名必须唯一；同一角色开多个实例是常态（多服务 / 多领域），所以名字要能区分。
- 名字含角色，路由时 `@mention` 可读、不歧义——`@BackendDev-user-service` 一眼知道是谁。
- **名字变化不改变行为，行为变化改 Instructions 不改名字**：换成员只改 `<成员标识>`、换项目只改 `<项目>`，模板原样复用。
- 命名是约束「流程可复用」的最后一块拼图：同一份 `squad.md`，换一组实例名就是一支新小队。
- **前缀通配解决「多实例共存」**：Squad 指令只写角色前缀（可复制），小队配置提供 suffix（可定位），二者分离既不破坏复用，又能在 workspace 里精确派活到本小队成员。
