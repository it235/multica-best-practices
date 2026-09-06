# 功能用例 → UI 一对一映射

## 条数

`N = len(json["functional"])`  
生成 `N` 个 test 函数，执行收集数必须为 `N`。

`case_id` → 方法名：非字母数字改 `_`，保证合法且唯一。

## 步骤

| 功能用例字段 | UI 脚本 |
| --- | --- |
| `preconditions` | fixture 或测试开头；登录文案用权限语义，密码只读环境变量 |
| `steps[i]` | 一个 Playwright 操作（click/fill/select/wait） |
| `expected_results[i]` | `expect(...)` 或 `assert`；与步骤同一 test 内紧跟 |

## locator

优先级：`get_by_role` → `get_by_label` → `get_by_text` → `get_by_placeholder`。  
禁止无页面依据的 CSS 选择器。  
打开 `page_url` 仍找不到 → `@pytest.mark.blocked` + skip。

## 不做

- 把「接口返回 200」写成 UI 断言（除非步骤就是看页面提示）
- 为跑通而删减步骤
- 跨用例共享可变全局状态
