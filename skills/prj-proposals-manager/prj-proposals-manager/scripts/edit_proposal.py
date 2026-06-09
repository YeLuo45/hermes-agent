#!/usr/bin/env python3
"""
提案/项目字段编辑脚本
提供交互式菜单编辑 proposal-index.md 和 CSV 文件中的字段。
所有修改必须通过此脚本进行，禁止直接写入文件。

用法:
    python3 scripts/edit_proposal.py proposal <proposal_id> [--field FIELD --value VALUE]
    python3 scripts/edit_proposal.py project <project_id> [--field FIELD --value VALUE]
    python3 scripts/edit_proposal.py interactive <type> <id>
    python3 scripts/edit_proposal.py list <type> [--filter FIELD=VALUE]
"""

import csv
import sys
import os
import re
import argparse
from datetime import datetime
from pathlib import Path

# 配置路径
PROPOSALS_ROOT = Path("/home/hermes/.hermes/proposals")
PROPOSALS_CSV = PROPOSALS_ROOT / "proposals.csv"
PROJECTS_CSV = PROPOSALS_ROOT / "projects.csv"
PROPOSAL_INDEX = PROPOSALS_ROOT / "proposal-index.md"
PROJECT_INDEX = PROPOSALS_ROOT / "project-index.md"

# 提案可编辑字段
PROPOSAL_FIELDS = {
    "title": "Title",
    "status": "Current Status",
    "owner": "Owner",
    "project_path": "Project Path",
    "prd_path": "PRD Path",
    "tech_solution": "Technical Solution",
    "test_cases": "Test Cases Path",
    "deployment_url": "Deployment URL",
    "deployment_branch": "Deployment Branch",
    "prd_confirmation": "PRD Confirmation",
    "tech_expectations": "Technical Expectations",
    "acceptance": "Acceptance",
    "research_direction": "Research Direction",
    "notes": "Notes",
    "last_update": "Last Update",
}

# 项目可编辑字段
PROJECT_FIELDS = {
    "name": "Name",
    "git_repo": "GitHub Repo",
    "description": "Description",
    "proposal_count": "Proposal Count",
    "last_update": "Last Update",
}

# 有效状态值
VALID_STATUSES = {
    "intake", "clarifying", "prd_pending_confirmation", "approved_for_dev",
    "in_tdd_test", "in_dev", "in_test_acceptance", "test_failed",
    "accepted", "needs_revision", "deployed", "deploying",
    "research_direction_pending", "active", "archived"
}
VALID_PRDS = {"pending", "confirmed", "timeout-approved", "rejected", ""}
VALID_TECH_EXPS = {"pending", "confirmed", "timeout-approved", ""}
VALID_ACCEPTANCES = {"pending", "accepted", "rejected", ""}


def log(msg):
    print(f"[edit-proposal] {msg}", file=sys.stderr)


def die(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)


def find_proposal_in_md(proposal_id, content):
    """在 proposal-index.md 中查找提案块"""
    pattern = rf'^### {re.escape(proposal_id)}:'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return None
    start = match.start()
    # 找到下一个 ### P- 标题或文件末尾
    next_match = re.search(r'^### P-\d{8}-\d{3}:', content[start + 1:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(content)
    return content[start:end]


def update_proposal_field_md(proposal_id, field_name, field_display_name, value):
    """更新 proposal-index.md 中的单个字段"""
    if not PROPOSAL_INDEX.exists():
        die(f"proposal-index.md 不存在: {PROPOSAL_INDEX}")

    with open(PROPOSAL_INDEX, "r", encoding="utf-8") as f:
        content = f.read()

    # 找到提案块
    block = find_proposal_in_md(proposal_id, content)
    if not block:
        die(f"未找到提案: {proposal_id}")

    # 检查字段是否存在
    field_pattern = rf"- `{re.escape(field_display_name)}`:\s*(.*)"
    field_match = re.search(field_pattern, block)

    if field_match:
        # 更新现有字段
        old_line_pattern = rf"- `{re.escape(field_display_name)}`:.*"
        new_line = f"- `{field_display_name}`: {value}"
        new_block = re.sub(old_line_pattern, new_line, block, count=1)
    else:
        # 添加新字段（在 block 末尾的 ### 之前）
        # 找到 block 中最后一个字段行，在其后插入
        last_field_match = re.search(r'- `[^`]+`:\s*.*', block)
        if last_field_match:
            insert_pos = last_field_match.end()
            new_block = block[:insert_pos] + f"\n- `{field_display_name}`: {value}" + block[insert_pos:]
        else:
            # 没有字段行，直接添加
            new_block = block + f"\n- `{field_display_name}`: {value}"

    # 替换原 block
    new_content = content.replace(block, new_block, 1)

    with open(PROPOSAL_INDEX, "w", encoding="utf-8") as f:
        f.write(new_content)

    log(f"✅ 已更新 {proposal_id} 的 {field_display_name} = {value}")


def update_proposal_csv(proposal_id, field_name, value):
    """更新 proposals.csv 中的字段"""
    if not PROPOSALS_CSV.exists():
        die(f"proposals.csv 不存在: {PROPOSALS_CSV}")

    rows = []
    updated = False

    with open(PROPOSALS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("id") == proposal_id:
                # 映射 field_name 到 CSV 列名
                csv_field = field_name  # 直接使用
                if csv_field in row:
                    old_val = row[csv_field]
                    row[csv_field] = value
                    updated = True
                    log(f"📝 CSV 更新: {proposal_id}.{csv_field}: '{old_val}' → '{value}'")
                else:
                    log(f"⚠️ 字段 {csv_field} 在 CSV 中不存在")
            rows.append(row)

    if updated:
        with open(PROPOSALS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log(f"✅ proposals.csv 已更新")
    else:
        die(f"未找到提案: {proposal_id}")


def update_project_field_md(project_id, field_name, field_display_name, value):
    """更新 project-index.md 中的单个字段"""
    if not PROJECT_INDEX.exists():
        die(f"project-index.md 不存在: {PROJECT_INDEX}")

    with open(PROJECT_INDEX, "r", encoding="utf-8") as f:
        content = f.read()

    # 找到项目块
    pattern = rf'^### {re.escape(project_id)}:'
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        die(f"未找到项目: {project_id}")

    start = match.start()
    next_match = re.search(r'^### PRJ-', content[start + 1:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(content)
    block = content[start:end]

    # 检查字段是否存在
    field_pattern = rf"- `{re.escape(field_display_name)}`:\s*(.*)"
    field_match = re.search(field_pattern, block)

    if field_match:
        old_line_pattern = rf"- `{re.escape(field_display_name)}`:.*"
        new_line = f"- `{field_display_name}`: {value}"
        new_block = re.sub(old_line_pattern, new_line, block, count=1)
    else:
        last_field_match = re.search(r'- `[^`]+`:\s*.*', block)
        if last_field_match:
            insert_pos = last_field_match.end()
            new_block = block[:insert_pos] + f"\n- `{field_display_name}`: {value}" + block[insert_pos:]
        else:
            new_block = block + f"\n- `{field_display_name}`: {value}"

    new_content = content.replace(block, new_block, 1)

    with open(PROJECT_INDEX, "w", encoding="utf-8") as f:
        f.write(new_content)

    log(f"✅ 已更新 {project_id} 的 {field_display_name} = {value}")


def update_project_csv(project_id, field_name, value):
    """更新 projects.csv 中的字段"""
    if not PROJECTS_CSV.exists():
        die(f"projects.csv 不存在: {PROJECTS_CSV}")

    rows = []
    updated = False

    with open(PROJECTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("id") == project_id:
                if field_name in row:
                    old_val = row[field_name]
                    row[field_name] = value
                    updated = True
                    log(f"📝 CSV 更新: {project_id}.{field_name}: '{old_val}' → '{value}'")
            rows.append(row)

    if updated:
        with open(PROJECTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log(f"✅ projects.csv 已更新")
    else:
        die(f"未找到项目: {project_id}")


def interactive_edit(proposal_or_project, id_value):
    """交互式编辑"""
    if proposal_or_project == "proposal":
        fields = PROPOSAL_FIELDS
    else:
        fields = PROJECT_FIELDS

    print(f"\n📝 交互式编辑 {proposal_or_project}: {id_value}")
    print("=" * 50)

    # 显示当前值
    print("\n当前字段值:")
    for key, display in list(fields.items())[:10]:
        print(f"  {key}: {display}")

    print("\n可编辑字段:")
    for i, (key, display) in enumerate(fields.items(), 1):
        print(f"  {i}. {key}")

    print("\n输入要编辑的字段名 (或 'q' 退出): ", end="")
    sys.stdout.flush()
    choice = sys.stdin.readline().strip()

    if choice.lower() == 'q':
        print("已取消")
        return

    if choice not in fields:
        die(f"未知字段: {choice}")

    field_display = fields[choice]
    print(f"\n当前值: ", end="")
    # 这里可以读取当前值，但简化起见直接让用户输入新值

    print(f"输入新值 (当前: N/A): ", end="")
    sys.stdout.flush()
    new_value = sys.stdin.readline().strip()

    if not new_value:
        die("值不能为空")

    # 执行更新
    if proposal_or_project == "proposal":
        update_proposal_field_md(id_value, choice, field_display, new_value)
        update_proposal_csv(id_value, choice, new_value)
    else:
        update_project_field_md(id_value, choice, field_display, new_value)
        update_project_csv(id_value, choice, new_value)


def list_items(item_type, filter_expr=None):
    """列出提案或项目"""
    if item_type == "proposal":
        csv_path = PROPOSALS_CSV
        id_pattern = r'^P-\d{8}-\d{3}$'
        id_col = "id"
    else:
        csv_path = PROJECTS_CSV
        id_pattern = r'^PRJ-\d{8}-\d{3}$'
        id_col = "id"

    if not csv_path.exists():
        die(f"{item_type}s.csv 不存在")

    # 解析过滤条件
    filter_field = None
    filter_value = None
    if filter_expr and "=" in filter_expr:
        filter_field, filter_value = filter_expr.split("=", 1)

    print(f"\n📋 {item_type} 列表")
    print("=" * 80)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 应用过滤
    if filter_field and filter_field in reader.fieldnames:
        rows = [r for r in rows if r.get(filter_field) == filter_value]
        print(f"过滤条件: {filter_field}={filter_value}")
        print(f"找到 {len(rows)} 条记录")
    else:
        print(f"共 {len(rows)} 条记录")

    print()
    print(f"{'ID':<20} {'Name/Title':<40} {'Status':<20}")
    print("-" * 80)

    for row in rows[:50]:  # 最多显示50条
        item_id = row.get(id_col, "")
        name = row.get("name", "") or row.get("title", "")
        status = row.get("status", "")
        print(f"{item_id:<20} {name[:38]:<40} {status:<20}")


def main():
    parser = argparse.ArgumentParser(description="提案/项目字段编辑工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # proposal 子命令
    proposal_parser = subparsers.add_parser("proposal", help="编辑提案字段")
    proposal_parser.add_argument("proposal_id", help="提案ID (P-YYYYMMDD-XXX)")
    proposal_parser.add_argument("--field", "-f", help="字段名")
    proposal_parser.add_argument("--value", "-v", help="字段值")

    # project 子命令
    project_parser = subparsers.add_parser("project", help="编辑项目字段")
    project_parser.add_argument("project_id", help="项目ID (PRJ-YYYYMMDD-XXX)")
    project_parser.add_argument("--field", "-f", help="字段名")
    project_parser.add_argument("--value", "-v", help="字段值")

    # interactive 子命令
    interactive_parser = subparsers.add_parser("interactive", help="交互式编辑")
    interactive_parser.add_argument("type", choices=["proposal", "project"], help="类型")
    interactive_parser.add_argument("id", help="ID")

    # list 子命令
    list_parser = subparsers.add_parser("list", help="列出提案/项目")
    list_parser.add_argument("type", choices=["proposal", "project"], help="类型")
    list_parser.add_argument("--filter", help="过滤条件 (field=value)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "interactive":
        interactive_edit(args.type, args.id)
        return

    if args.command == "list":
        list_items(args.type, args.filter)
        return

    # proposal/project 编辑
    if args.command == "proposal":
        if not args.field or not args.value:
            die("必须指定 --field 和 --value")
        if args.field not in PROPOSAL_FIELDS:
            die(f"未知提案字段: {args.field}，可用: {', '.join(PROPOSAL_FIELDS.keys())}")
        field_display = PROPOSAL_FIELDS[args.field]

        # 验证状态值
        if args.field == "status" and args.value not in VALID_STATUSES:
            log(f"⚠️  状态值 {args.value} 不在标准列表中: {VALID_STATUSES}")
        elif args.field == "prd_confirmation" and args.value not in VALID_PRDS:
            log(f"⚠️  PRD确认值 {args.value} 不在标准列表中")
        elif args.field == "tech_expectations" and args.value not in VALID_TECH_EXPS:
            log(f"⚠️  技术期望值 {args.value} 不在标准列表中")
        elif args.field == "acceptance" and args.value not in VALID_ACCEPTANCES:
            log(f"⚠️  验收值 {args.value} 不在标准列表中")

        # 更新 md 和 csv
        update_proposal_field_md(args.proposal_id, args.field, field_display, args.value)
        update_proposal_csv(args.proposal_id, args.field, args.value)

    elif args.command == "project":
        if not args.field or not args.value:
            die("必须指定 --field 和 --value")
        if args.field not in PROJECT_FIELDS:
            die(f"未知项目字段: {args.field}，可用: {', '.join(PROJECT_FIELDS.keys())}")
        field_display = PROJECT_FIELDS[args.field]

        update_project_field_md(args.project_id, args.field, field_display, args.value)
        update_project_csv(args.project_id, args.field, args.value)


if __name__ == "__main__":
    main()
