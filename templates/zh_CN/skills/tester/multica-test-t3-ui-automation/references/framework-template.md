# 从零框架（pytest + Playwright + Allure）

目标目录为空或不存在时，Agent **必须原样创建**下列结构（可替换 `{JIRA_KEY}`）。

```text
<target_dir>/
├── README.md
├── requirements.txt
├── pytest.ini
├── conftest.py
├── config/
│   ├── env.yaml.example
│   └── env.yaml              # gitignore；base_url 来自评论 deploy/page_url
├── tests/
│   └── __init__.py
├── artifacts/
└── .gitignore
```

## requirements.txt

```text
pytest>=8.0
playwright>=1.45
pytest-playwright>=0.5
PyYAML>=6.0
allure-pytest>=2.13
python-dotenv>=1.0
```

## pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -ra --strict-markers
markers =
    ui: UI automation
    blocked: missing locator or data
```

## conftest.py（要点）

- `pytest_playwright` 的 `page` fixture
- session 级读 `config/env.yaml` 的 `base_url`
- 禁止在 conftest 写死账号密码；登录凭据来自环境变量名

## config/env.yaml.example

```yaml
base_url: "https://replace-from-issue-comment"
browser: chromium
headless: true
timeout_ms: 30000
```

## .gitignore

```text
.venv/
__pycache__/
.pytest_cache/
config/env.yaml
.env
artifacts/allure-results/
artifacts/allure-report/
```

## README.md 须写

```text
1:1 来源：multica-test-t1-design functional JSON
执行：.venv/Scripts/pytest tests/ --alluredir artifacts/allure-results
```
