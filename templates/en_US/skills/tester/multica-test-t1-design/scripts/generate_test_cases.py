#!/usr/bin/env python3
"""
Test Case Generator Script
辅助生成结构化测试用例的脚本，提供标准化的输出格式。
强制要求每个用例标注覆盖维度（全量场景 / 边界场景 / 页面检查）。
"""

from dataclasses import dataclass, field
from typing import Optional
import json, re, sys

# Fix Windows terminal encoding for Chinese output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 覆盖维度常量
DIMENSION_FULL = "全量场景"       # 所有业务路径
DIMENSION_BOUNDARY = "边界场景"    # 边界值/临界条件
DIMENSION_UI = "页面检查"          # UI 界面/交互检查

VALID_DIMENSIONS = {DIMENSION_FULL, DIMENSION_BOUNDARY, DIMENSION_UI}


# ============================================================
# Data Models
# ============================================================

@dataclass
class FunctionalTestCase:
    """功能测试用例数据模型"""
    case_id: str
    module: str
    coverage_dimension: str  # 全量场景 / 边界场景 / 页面检查
    title: str
    preconditions: list[str]
    test_data: str
    case_type: str  # 功能流程/输入验证/UI检查/边界值/异常场景
    priority: str   # P1 核心 / P2 正常 / P3 异常或边界（禁止默认 P0）
    steps: list[str]
    expected_results: list[str]

    def __post_init__(self):
        if self.coverage_dimension not in VALID_DIMENSIONS:
            raise ValueError(
                f"coverage_dimension 必须是以下之一: {VALID_DIMENSIONS}"
            )


@dataclass
class ApiTestCase:
    """接口测试用例数据模型"""
    case_id: str
    api_name: str
    api_endpoint: str
    coverage_dimension: str  # 全量场景 / 边界场景 / 页面检查
    title: str
    method: str  # GET/POST/PUT/DELETE
    preconditions: list[str]
    request_params: dict
    expected_status_code: int
    expected_biz_code: Optional[int] = None
    expected_response_body: dict = field(default_factory=dict)
    validation_points: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.coverage_dimension not in VALID_DIMENSIONS:
            raise ValueError(
                f"coverage_dimension 必须是以下之一: {VALID_DIMENSIONS}"
            )


# ============================================================
# Formatters
# ============================================================

def format_module_header(module_name: str, full_scenes: list[str],
                         boundary_scenes: list[str],
                         ui_checks: list[str]) -> str:
    """格式化模块的覆盖矩阵头"""
    lines = [
        "=" * 60,
        f"模块: {module_name}",
        "=" * 60,
        "[覆盖矩阵]",
    ]
    if full_scenes:
        lines.append(f"  ┌ {DIMENSION_FULL}: {' / '.join(full_scenes)}")
    if boundary_scenes:
        lines.append(f"  ┌ {DIMENSION_BOUNDARY}: {' / '.join(boundary_scenes)}")
    if ui_checks:
        lines.append(f"  ┌ {DIMENSION_UI}: {' / '.join(ui_checks)}")
    lines.append("")
    return "\n".join(lines)


def format_functional_case(tc: FunctionalTestCase) -> str:
    """格式化输出功能测试用例"""
    lines = [
        "-" * 60,
        f"用例编号: {tc.case_id}",
        f"所属模块: {tc.module}",
        f"覆盖维度: {tc.coverage_dimension}",
        f"测试标题: {tc.title}",
        f"用例类型: {tc.case_type}",
        f"优先级:   {tc.priority}",
        "",
        "前置条件:",
    ]
    for i, cond in enumerate(tc.preconditions, 1):
        lines.append(f"  {i}. {cond}")

    lines.extend(["", f"测试数据: {tc.test_data}", ""])

    lines.append("测试步骤:")
    for i, step in enumerate(tc.steps, 1):
        lines.append(f"  {i}. {step}")

    lines.append("")
    lines.append("预期结果:")
    for i, res in enumerate(tc.expected_results, 1):
        lines.append(f"  {i}. {res}")

    lines.append("")
    return "\n".join(lines)


def format_api_case(tc: ApiTestCase) -> str:
    """格式化输出接口测试用例"""
    lines = [
        "-" * 60,
        f"用例编号: {tc.case_id}",
        f"接口名称: {tc.method} {tc.api_endpoint}",
        f"覆盖维度: {tc.coverage_dimension}",
        f"测试标题: {tc.title}",
        f"请求方式: {tc.method}",
        "",
        "前置条件:",
    ]
    for i, cond in enumerate(tc.preconditions, 1):
        lines.append(f"  {i}. {cond}")

    lines.extend(["", "请求参数:", json.dumps(tc.request_params, ensure_ascii=False, indent=2), ""])
    lines.append(f"预期状态码: {tc.expected_status_code}")
    if tc.expected_biz_code is not None:
        lines.append(f"预期业务码: {tc.expected_biz_code}")
    lines.extend(["", "预期响应体:", json.dumps(tc.expected_response_body, ensure_ascii=False, indent=2), ""])

    lines.append("校验点:")
    for pt in tc.validation_points:
        lines.append(f"  - {pt}")

    lines.append("")
    return "\n".join(lines)


def format_dedup_report(skipped: int, ambiguous: int, details: list[dict]) -> str:
    """格式化去重报告"""
    lines = [
        "",
        "[去重报告]",
        f"  自动跳过（重复）: {skipped} 个",
        f"  标记存疑: {ambiguous} 个",
    ]
    for d in details:
        tc = d.get("test_case", {})
        match = d.get("best_match", {})
        sim = d.get("similarity", 0)
        lines.append(
            f"    {tc.get('title', '?')[:50]} → "
            f"匹配 {match.get('key', '?')} ({sim:.0%})"
        )
    return "\n".join(lines)


def clean_wiki_markers(text: str) -> str:
    """清理 Confluence wiki 标记符（如 {LQ}{RQ}），确保用例可读。

    这些标记在 Confluence HTML→Markdown 转换后可能以纯文本保留，
    出现在测试用例中会导致用户无法理解。
    """
    text = re.sub(r'\{LQ\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\{RQ\}', '', text, flags=re.IGNORECASE)
    return text


def validate_steps_expected(tc) -> None:
    """校验 steps 和 expected_results 对应关系，不一致时记录警告但不中断

    注意：预期结果可以包含多个验证点（使用编号 1）2）3）组织），
    但必须保证每条步骤都有对应的预期结果，禁止空预期结果。
    某条用例的校验问题不影响其他用例的正常生成。
    """
    steps = tc.get("steps", [])
    expected = tc.get("expected_results", [])
    if not steps:
        return
    if not expected:
        print(f"WARNING: case_id={tc.get('case_id', '?')} title={tc.get('title', '?')} "
              f"有步骤但预期结果为空，标记记录")
        return
    # 检查是否存在空字符串预期结果
    for i, (step, exp) in enumerate(zip(steps, expected)):
        if not exp or not exp.strip():
            print(f"WARNING: case_id={tc.get('case_id', '?')} "
                  f"步骤{i+1}='{step[:30]}' 预期结果为空，已标记")


def print_coverage_checklist(modules: dict[str, dict[str, bool]],
                              uncovered_notes: str = ""):
    """输出模块级覆盖检查表"""
    lines = ["", "=" * 60, "覆盖检查报告", "=" * 60]
    for module_name, dims in modules.items():
        lines.append(f"\n模块: {module_name}")
        for dim, covered in dims.items():
            mark = "✓" if covered else " "
            lines.append(f"  [{mark}] {dim}")
    if uncovered_notes:
        lines.append(f"\n未覆盖说明: {uncovered_notes}")
    print("\n".join(lines))


# ============================================================
# Example usage
# ============================================================

if __name__ == "__main__":
    # Demo: module header
    print(format_module_header(
        module_name="用户登录",
        full_scenes=["正常登录", "密码错误", "用户不存在", "账号锁定", "记住密码"],
        boundary_scenes=["空用户名", "空密码", "超长密码100字符", "连续失败5次"],
        ui_checks=["登录页布局", "输入框悬停态", "错误提示位置", "按钮禁用态"],
    ))

    # Demo: functional test case
    ftc = FunctionalTestCase(
        case_id="TC-F-LOGIN-001",
        module="用户登录",
        coverage_dimension=DIMENSION_FULL,
        title="验证使用正确的用户名和密码可以成功登录",
        preconditions=["用户已注册且账号状态正常", "浏览器已打开登录页面"],
        test_data="用户名: testuser@example.com, 密码: Abc@123456",
        case_type="功能流程",
        priority="P1",
        steps=[
            "在用户名输入框中输入 testuser@example.com",
            "在密码输入框中输入 Abc@123456",
            "点击'登录'按钮",
        ],
        expected_results=[
            "输入框正常显示输入内容",
            "密码显示为掩码形式",
            "登录成功，跳转到首页",
        ],
    )
    print(format_functional_case(ftc))

    print(print_coverage_checklist(
        {
            "用户登录": {
                DIMENSION_FULL: True,
                DIMENSION_BOUNDARY: True,
                DIMENSION_UI: True,
            },
            "商品列表": {
                DIMENSION_FULL: True,
                DIMENSION_BOUNDARY: False,
                DIMENSION_UI: True,
            },
        },
        uncovered_notes="商品列表缺少分页边界场景 (缺少接口文档)",
    ))
