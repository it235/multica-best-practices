# multica-manage-skills 使用说明

通过 Multica API 管理 Skill（创建 / 更新 / 发布 / 删除）。所有 API 地址均为占位，使用方在环境变量填入自己的 Multica 地址与 token。

## 1. 配置环境变量

```bash
export MULTICA_API_URL="https://your-multica.example.com"   # 占位地址
export MULTICA_API_TOKEN="mul_xxxxxxxxxxxxxxxx"             # 你的 API token
```

`scripts/multica_api.py` 优先读 `MULTICA_API_URL`，未设置时报错提示填入。

## 2. 安装依赖

```bash
cd scripts
pip install requests   # 唯一依赖
```

## 3. 主要用法

```bash
# 列出所有 skill
python scripts/multica_api.py list

# 上传 / 更新一个 skill 目录
python scripts/multica_api.py push --path /path/to/your-skill

# 删除
python scripts/multica_api.py delete --name your-skill-name
```

API 字段与响应结构见 `references/api_reference.md`。

## 4. 注意事项

- `MULTICA_API_TOKEN` 为敏感凭据，**不要提交**，建议放 shell 环境或 secrets 管理。
- `MULTICA_API_URL` 不要写真实生产地址进仓库。
