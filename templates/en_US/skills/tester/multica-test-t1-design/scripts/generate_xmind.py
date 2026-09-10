#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将测试用例 JSON 导出为 XMind 2020+ 格式 (.xmind)
兼容 XMind 2020 / XMind 8 / MindMaster / 百度脑图

格式说明（匹配 test_cases_PROJ-123.xmind 参考格式）:
  - 根主题标题 = 项目名称（如 MDP、PROJ）
  - 模块主题以 / 结尾表示文件夹
  - 支持多层模块嵌套（模块名用 / 分隔）
  - 用例结构：前置条件（第一子节点）+ 步骤（含预期作为子节点）
  - 优先级标记：P1→priority-1, P2→priority-2, P3→priority-3（兼容历史 P0→priority-1、P4→priority-3）

  content.json: [
    {"id":"s1","class":"sheet","rootTopic":{"id":"root","title":"MDP","children":{"attached":[...]}}}
  ]
  metadata.json: {"dataStructureVersion":"3","layoutEngineVersion":"5","creator":{...}}
  manifest.json: {"file-entries":{"content.json":{},"metadata.json":{}}}
"""
import json, os, sys, zipfile, uuid, re

# Fix Windows terminal encoding for Chinese output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def _make_id():
    return uuid.uuid4().hex[:24]


def strip_module_prefix(name):
    """Strip ID prefix like 'FR-01 ' from module names, keep clean name"""
    return re.sub(r'^[A-Z]+-\d+\s+', '', name)


def build_topic_json(title, children=None, tid=None, markers=None):
    """构建单个 topic 的 JSON dict"""
    topic = {
        "id": tid or _make_id(),
        "title": title,
    }
    if children:
        topic["children"] = {"attached": children}
    if markers:
        topic["markers"] = markers
    return topic


def build_case_json(case_title, preconditions, steps, expected_results, priority):
    """构建一个测试用例的 JSON 结构

    格式（匹配 test_cases_PROJ-123.xmind）:
    {
      "id": "xxx",
      "title": "用例标题",
      "children": {
        "attached": [
          {"title": "前置条件：xxx"},
          {
            "title": "步骤",
            "children": {"attached": [
              {"title": "预期：xxx"}
            ]}
          }
        ]
      },
      "markers": [{"markerId": "priority-1"}]
    }
    """
    children = []

    # 前置条件
    if preconditions:
        pc_text = "；".join(p[:100] for p in preconditions)
        children.append(build_topic_json(f"前置条件：{pc_text}"))

    # 严格校验预期结果数量
    if len(steps) != len(expected_results):
        raise ValueError(
            f"步骤与预期结果数量不一致！case_title='{case_title}' "
            f"steps={len(steps)} expected_results={len(expected_results)}\n"
            f"禁止自动填充预期结果，请修改生成逻辑后重试。"
        )

    # 步骤 + 预期结果（每个步骤一一对应，完整输出）
    # 预期结果支持多行编号格式：1）xxx\n\n2）xxx\n\n3）xxx（仍属于同一个预期结果）
    for i, step in enumerate(steps):
        exp_text = expected_results[i]
        exp_list = [build_topic_json(f"预期：{exp_text}")]
        step_node = build_topic_json(step, children=exp_list)
        children.append(step_node)

    # 优先级映射
    priority_map = {
        "P0": "priority-1",
        "P1": "priority-1",
        "P2": "priority-2",
        "P3": "priority-3",
        "P4": "priority-3",
    }
    marker_id = priority_map.get(priority, "priority-3")
    markers = [{"markerId": marker_id}]

    return build_topic_json(case_title, children=children, tid=_make_id(), markers=markers)


def build_module_tree(modules):
    """将扁平的模块列表转换为嵌套的树形结构，支持多级模块路径

    modules: [(mod_name, [case_tuple, ...]), ...]
      case_tuple = (title, preconditions, steps, expected, priority)
      mod_name 可为 "父模块/子模块" 表示嵌套

    返回: 根级 topic JSON 列表（模块名以 / 结尾）
    """
    tree = {}
    for mod_name, cases in modules:
        parts = [p.strip() for p in mod_name.split("/")]
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        leaf = parts[-1]
        if leaf not in current:
            current[leaf] = []
        current[leaf].extend(cases)

    def _serialize(subtree):
        topics = []
        for name, children in sorted(subtree.items()):
            if isinstance(children, list):
                case_list = [build_case_json(*c) for c in children]
                topics.append(build_topic_json(f"{name}/", children=case_list))
            else:
                child_topics = _serialize(children)
                topics.append(build_topic_json(f"{name}/", children=child_topics))
        return topics

    return _serialize(tree)


def build_sheet_json(sheet_title, root_title, module_topics):
    """构建一个 Sheet 的 JSON

    module_topics: build_module_tree 返回的 topic 列表
    """
    root_topic = build_topic_json(root_title, children=module_topics)
    return {
        "id": "s1",
        "class": "sheet",
        "rootTopic": root_topic,
    }


def group_by_module(test_cases):
    modules = {}
    for tc in test_cases:
        mod = tc.get("module", "未分类")
        modules.setdefault(mod, []).append(tc)
    return sorted(modules.items(), key=lambda x: x[0])


def build_functional_sheets(data, project_key):
    """构建功能测试 Sheet"""
    func_cases = data.get("functional", [])
    if not func_cases:
        return None

    modules = group_by_module(func_cases)
    sheet_module_tuples = []
    for mod_name, cases in modules:
        module_cases = []
        clean_mod = strip_module_prefix(mod_name)  # "FR-01 文件条目增删改" -> "文件条目增删改"
        for c in cases:
            title = c.get("title", "")
            preconditions = c.get("preconditions", [])
            steps = c.get("steps", [])
            expected = c.get("expected_results", [])
            pri = c.get("priority", "")
            module_cases.append((title, preconditions, steps, expected, pri))
        sheet_module_tuples.append((clean_mod, module_cases))

    module_topics = build_module_tree(sheet_module_tuples)
    return build_sheet_json("功能测试用例", project_key, module_topics)


def build_api_sheets(data, project_key):
    """构建接口测试 Sheet"""
    api_cases = data.get("api", [])
    if not api_cases:
        return None

    seen_apis = {}
    for tc in api_cases:
        name = tc.get("module", tc.get("api_name", "未分类"))
        seen_apis.setdefault(name, []).append(tc)
    api_modules = sorted(seen_apis.items(), key=lambda x: x[0])

    sheet_module_tuples = []
    for mod_name, cases in api_modules:
        module_cases = []
        clean_mod = strip_module_prefix(mod_name)
        for c in cases:
            method = c.get("method", "")
            endpoint = c.get("api_endpoint", "")
            title = c.get("title", "")
            case_id = c.get("case_id", "")
            pri = c.get("priority", "P3")
            if endpoint:
                label = f"{case_id} [{method}] {endpoint} - {title}"
            else:
                label = f"{case_id} - {title}"
            steps = [f"请求参数: {k}={v}" for k, v in c.get("request_params", {}).items()][:5]
            expected = c.get("validation_points", [])
            preconditions = c.get("preconditions", [])
            module_cases.append((label, preconditions, steps, expected, pri))
        sheet_module_tuples.append((clean_mod, module_cases))

    module_topics = build_module_tree(sheet_module_tuples)
    return build_sheet_json("接口测试用例", project_key, module_topics)


def extract_jira_key(data):
    """从用例 JSON 中提取完整需求编号（如 PROJ-100）"""
    if not isinstance(data, dict):
        return ""
    for field in ("jira_key", "parent_issue"):
        key = (data.get(field) or "").strip()
        if key and re.match(r'^[A-Z]+-\d+$', key):
            return key
        m = re.search(r'([A-Z]+-\d+)', key)
        if m:
            return m.group(1)
    return ""


def resolve_output_path(input_json, output_xmind, jira_key):
    """解析输出路径：文件名必须带需求编号；仅写入目标文件，不删除其他 .xmind。

    命名约定：test_cases_{JIRA_KEY}.xmind（如 test_cases_PROJ-100.xmind）
    """
    input_dir = os.path.dirname(os.path.abspath(input_json)) or "."

    if not output_xmind:
        name = f"test_cases_{jira_key}.xmind" if jira_key else "test_cases.xmind"
        return os.path.join(input_dir, name)

    # 若传入的是目录，在目录下按需求编号落盘
    if os.path.isdir(output_xmind):
        name = f"test_cases_{jira_key}.xmind" if jira_key else "test_cases.xmind"
        return os.path.join(output_xmind, name)

    out_dir = os.path.dirname(os.path.abspath(output_xmind)) or input_dir
    base = os.path.basename(output_xmind)
    name, ext = os.path.splitext(base)
    if not ext:
        ext = ".xmind"

    # 文件名未含需求编号时自动补上，避免固定名 test_cases.xmind 覆盖混淆
    if jira_key and jira_key not in base:
        base = f"{name}_{jira_key}{ext}"
        return os.path.join(out_dir, base)

    return output_xmind


def generate(input_json, output_xmind=None, project_key=None):
    """生成 XMind 文件

    Args:
        input_json: 测试用例 JSON 文件路径
        output_xmind: 输出 .xmind 文件路径；为 None 时按 jira_key 自动命名为
            test_cases_{JIRA_KEY}.xmind。仅覆盖当前目标文件，不删除其他需求的旧文件。
        project_key: 项目标识（用作根主题标题）。默认为 None，会自动从数据中的 jira_key 提取前缀

    Returns:
        (success: bool, output_path: str|None)
    """
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        test_cases = data
    else:
        test_cases = {"functional": [], "api": []}
        for tc in data:
            tc_type = tc.get("type", "")
            if tc_type == "api":
                test_cases.setdefault("api", []).append(tc)
            else:
                test_cases.setdefault("functional", []).append(tc)

    jira_key = extract_jira_key(test_cases)

    # 自动从 jira_key 中提取系统前缀作为根节点标题（如 PROJ-100 → PROJ）
    if project_key is None:
        if jira_key:
            m = re.match(r'([A-Z]+)-\d+', jira_key)
            project_key = m.group(1) if m else "MDP"
        else:
            project_key = "MDP"

    sheets = []
    func_sheet = build_functional_sheets(test_cases, project_key)
    if func_sheet:
        sheets.append(func_sheet)
    # 接口用例不生成 XMind，仅保存本地 JSON 文件
    if not sheets:
        print("错误: 没有找到测试用例数据", file=sys.stderr)
        return False, None

    output_path = resolve_output_path(input_json, output_xmind, jira_key)
    # 只写入/覆盖当前需求对应文件；禁止删除同目录其他 .xmind
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    content_json = json.dumps(sheets, ensure_ascii=False, indent=2)

    metadata_json = json.dumps({
        "dataStructureVersion": "3",
        "layoutEngineVersion": "5",
        "creator": {
            "name": "TestCaseGenerator",
            "version": "1.0"
        }
    }, ensure_ascii=False, indent=2)

    manifest_json = json.dumps({
        "file-entries": {
            "content.json": {},
            "metadata.json": {}
        }
    }, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.json', content_json.encode('utf-8'))
        zf.writestr('metadata.json', metadata_json.encode('utf-8'))
        zf.writestr('manifest.json', manifest_json.encode('utf-8'))

    return True, output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="导出测试用例为 XMind 2020+ 格式（文件名含需求编号，不删除旧文件）"
    )
    parser.add_argument("--input", "-i", required=True, help="测试用例 JSON 文件路径")
    parser.add_argument(
        "--output", "-o", default=None,
        help="输出 .xmind 路径；省略则自动命名为 test_cases_{JIRA_KEY}.xmind。"
             "若传入 test_cases.xmind 且 JSON 含 jira_key，会自动改为 test_cases_{JIRA_KEY}.xmind",
    )
    parser.add_argument("--project", "-p", default=None, help="项目名称/标识（用作根主题标题，默认自动从 jira_key 提取）")
    args = parser.parse_args()

    success, out_path = generate(args.input, args.output, project_key=args.project)
    if success and out_path:
        size = os.path.getsize(out_path)
        print(f"XMind 已生成: {out_path} ({size/1024:.1f} KB)")
        print("  说明: 仅写入当前需求文件，未删除同目录其他 .xmind")
        with zipfile.ZipFile(out_path, 'r') as zf:
            print(f"  包含: {', '.join(zf.namelist())}")
    else:
        sys.exit(1)
