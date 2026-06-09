#!/usr/bin/env python3
"""
提案系统数据管理 CLI
所有项目和提案的增删改必须通过此脚本进行，禁止直接写入 CSV。
"""

import csv
import sys
import os
import re
import argparse
from datetime import datetime
from pathlib import Path

# 配置路径（使用硬编码，不依赖 Path.home()）
PROPOSALS_ROOT = Path("/home/hermes/.hermes/proposals")
PROJECTS_CSV = PROPOSALS_ROOT / "projects.csv"
PROPOSALS_CSV = PROPOSALS_ROOT / "proposals.csv"
MAPPING_CSV = PROPOSALS_ROOT / "project_proposal_mapping.csv"

# 有效枚举值
VALID_PROPOSAL_STATUSES = {
    "intake", "clarifying", "prd_pending_confirmation", "approved_for_dev",
    "in_tdd_test", "in_dev", "in_test_acceptance", "test_failed",
    "accepted", "needs_revision", "deployed", "deploying",
    "research_direction_pending", "active", "archived"
}
VALID_PROPOSAL_STAGES = {"ideation", "development", "research", "proposal"}
VALID_PRDS = {"pending", "confirmed", "timeout-approved", "rejected", ""}
VALID_TECH_EXPS = {"pending", "confirmed", "timeout-approved", ""}
VALID_ACCEPTANCES = {"pending", "accepted", "rejected", ""}
VALID_GAME_TYPES = {"", "休闲", "策略", "卡牌", "RPG", "消除", "塔防", "模拟", "动作", "射击"}

# 项目ID格式: PRJ-YYYYMMDD-XXX
PROJECT_ID_PATTERN = re.compile(r'^PRJ-\d{8}-\d{3}$')
# 提案ID格式: P-YYYYMMDD-XXX
PROPOSAL_ID_PATTERN = re.compile(r'^P-\d{8}-\d{3}$')


def log(msg):
    print(f"[proposal-manager] {msg}", file=sys.stderr)


def die(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)


def read_csv(path):
    """读取CSV，返回 (header, rows)"""
    if not path.exists():
        return [], []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def write_csv(path, headers, rows):
    """写入CSV，保留header顺序"""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def load_projects():
    """加载所有项目"""
    headers, rows = read_csv(PROJECTS_CSV)
    return headers, rows


def load_proposals():
    """加载所有提案"""
    headers, rows = read_csv(PROPOSALS_CSV)
    return headers, rows


def load_mapping():
    """加载映射表"""
    headers, rows = read_csv(MAPPING_CSV)
    return headers, rows


# ==================== 校验函数 ====================

def validate_project_id(project_id):
    """校验项目ID格式"""
    if not PROJECT_ID_PATTERN.match(project_id):
        raise ValueError(f"项目ID格式错误: {project_id}，期望格式: PRJ-YYYYMMDD-XXX")


def validate_proposal_id(proposal_id):
    """校验提案ID格式"""
    if not PROPOSAL_ID_PATTERN.match(proposal_id):
        raise ValueError(f"提案ID格式错误: {proposal_id}，期望格式: P-YYYYMMDD-XXX")


def validate_non_empty(value, field_name):
    """校验非空字符串"""
    if not value or not str(value).strip():
        raise ValueError(f"{field_name} 不能为空")


def validate_enum(value, field_name, valid_values):
    """校验枚举值"""
    if value not in valid_values:
        raise ValueError(f"{field_name} 值非法: {value}，有效值: {valid_values}")


def validate_url_or_empty(value, field_name):
    """校验URL格式（可为空）"""
    if value and not value.strip():
        return  # 空字符串OK
    if value and not (value.startswith('http://') or value.startswith('https://') or value.startswith('git@')):
        raise ValueError(f"{field_name} 格式错误: {value}，需以 http:// https:// 或 git@ 开头")


def validate_project_data(data):
    """校验项目数据"""
    errors = []
    
    # 必填字段
    if 'id' not in data or not data['id']:
        errors.append("缺少必填字段: id")
    elif not PROJECT_ID_PATTERN.match(data['id']):
        errors.append(f"id 格式错误: {data['id']}，期望 PRJ-YYYYMMDD-XXX")
    
    if 'name' not in data or not data['name']:
        errors.append("缺少必填字段: name")
    
    # 可选字段校验
    if 'git_repo' in data and data['git_repo']:
        validate_url_or_empty(data['git_repo'], 'git_repo')
    
    if errors:
        raise ValueError("; ".join(errors))


def validate_proposal_data(data, is_new=True):
    """校验提案数据"""
    errors = []
    
    # 必填字段
    if 'id' not in data or not data['id']:
        errors.append("缺少必填字段: id")
    elif not PROPOSAL_ID_PATTERN.match(data['id']):
        errors.append(f"id 格式错误: {data['id']}，期望 P-YYYYMMDD-XXX")
    
    if 'title' not in data or not data['title']:
        errors.append("缺少必填字段: title")
    
    if 'project_id' not in data or not data['project_id']:
        errors.append("缺少必填字段: project_id")
    elif not PROJECT_ID_PATTERN.match(data['project_id']):
        errors.append(f"project_id 格式错误: {data['project_id']}，期望 PRJ-YYYYMMDD-XXX")
    
    if 'status' not in data or not data['status']:
        errors.append("缺少必填字段: status")
    elif data['status'] not in VALID_PROPOSAL_STATUSES:
        errors.append(f"status 值非法: {data['status']}，有效值: {VALID_PROPOSAL_STATUSES}")
    
    # 枚举字段校验
    if 'prd_confirmation' in data and data['prd_confirmation']:
        if data['prd_confirmation'] not in VALID_PRDS:
            errors.append(f"prd_confirmation 值非法: {data['prd_confirmation']}")
    
    if 'tech_expectations' in data and data['tech_expectations']:
        if data['tech_expectations'] not in VALID_TECH_EXPS:
            errors.append(f"tech_expectations 值非法: {data['tech_expectations']}")
    
    if 'acceptance' in data and data['acceptance']:
        if data['acceptance'] not in VALID_ACCEPTANCES:
            errors.append(f"acceptance 值非法: {data['acceptance']}")
    
    if 'stage' in data and data['stage']:
        if data['stage'] not in VALID_PROPOSAL_STAGES:
            errors.append(f"stage 值非法: {data['stage']}")
    
    if 'git_repo' in data and data['git_repo']:
        validate_url_or_empty(data['git_repo'], 'git_repo')
    
    if 'deployment_url' in data and data['deployment_url']:
        validate_url_or_empty(data['deployment_url'], 'deployment_url')
    
    if 'game_type' in data and data['game_type']:
        if data['game_type'] not in VALID_GAME_TYPES:
            errors.append(f"game_type 值非法: {data['game_type']}")
    
    if errors:
        raise ValueError("; ".join(errors))


def validate_project_exists(project_id, projects):
    """校验项目是否存在"""
    for p in projects:
        if p['id'] == project_id:
            return True
    raise ValueError(f"项目不存在: {project_id}")


def validate_proposal_exists(proposal_id, proposals):
    """校验提案是否存在"""
    for p in proposals:
        if p['id'] == proposal_id:
            return True
    raise ValueError(f"提案不存在: {proposal_id}")


def get_project_by_id(project_id, projects):
    """根据ID获取项目"""
    for p in projects:
        if p['id'] == project_id:
            return p
    return None


def get_proposal_by_id(proposal_id, proposals):
    """根据ID获取提案"""
    for p in proposals:
        if p['id'] == proposal_id:
            return p
    return None


# ==================== 项目操作 ====================

def generate_project_id(projects):
    """生成下一个项目ID: PRJ-YYYYMMDD-XXX"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"PRJ-{today}-"
    max_num = 0
    for p in projects:
        if p['id'].startswith(prefix):
            try:
                num = int(p['id'].split('-')[-1])
                max_num = max(max_num, num)
            except:
                pass
    return f"{prefix}{max_num + 1:03d}"


def cmd_add_project(args):
    """新增项目"""
    headers, projects = load_projects()
    
    # 生成ID（如果未指定）
    project_id = args.id
    if not project_id:
        project_id = generate_project_id(projects)
        log(f"自动生成项目ID: {project_id}")
    
    data = {
        'id': project_id,
        'name': args.name,
        'proposal_count': '0',
        'git_repo': args.git_repo or '',
    }
    
    # 校验数据
    validate_project_data(data)
    
    # 检查ID重复
    for p in projects:
        if p['id'] == project_id:
            die(f"项目ID已存在: {project_id}")
    
    # 写入
    if not headers:
        headers = ['id', 'name', 'proposal_count', 'git_repo']
    projects.append(data)
    write_csv(PROJECTS_CSV, headers, projects)
    
    log(f"新增项目成功: {project_id} - {args.name}")
    print(project_id)


def cmd_list_projects(args):
    """列出项目"""
    headers, projects = load_projects()
    
    if not projects:
        log("暂无项目")
        return
    
    # 确定输出字段
    fields = args.fields.split(',') if args.fields else headers
    # 过滤掉不存在的字段
    fields = [f for f in fields if f in headers]
    
    # 打印表头
    print('\t'.join(fields))
    
    # 打印数据
    for p in projects:
        row = [p.get(f, '') for f in fields]
        print('\t'.join(row))


def cmd_get_project(args):
    """获取单个项目"""
    _, projects = load_projects()
    
    p = get_project_by_id(args.id, projects)
    if not p:
        die(f"项目不存在: {args.id}")
    
    if args.json:
        import json
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        for k, v in p.items():
            print(f"{k}: {v}")


def cmd_update_project(args):
    """更新项目"""
    headers, projects = load_projects()
    
    p = get_project_by_id(args.id, projects)
    if not p:
        die(f"项目不存在: {args.id}")
    
    # 更新字段
    if args.name is not None:
        if not args.name:
            raise ValueError("name 不能为空")
        p['name'] = args.name
    
    if args.git_repo is not None:
        if args.git_repo:
            validate_url_or_empty(args.git_repo, 'git_repo')
        p['git_repo'] = args.git_repo
    
    # 重新校验
    validate_project_data(p)
    
    write_csv(PROJECTS_CSV, headers, projects)
    log(f"更新项目成功: {args.id}")


def cmd_delete_project(args):
    """删除项目（软删除：只修改状态）"""
    headers, projects = load_projects()
    
    p = get_project_by_id(args.id, projects)
    if not p:
        die(f"项目不存在: {args.id}")
    
    if not args.force:
        # 检查是否有活跃提案
        _, proposals = load_proposals()
        active_count = 0
        for pr in proposals:
            if pr['project_id'] == args.id and pr.get('status') not in ('archived', 'deployed'):
                active_count += 1
        if active_count > 0:
            die(f"项目下有 {active_count} 个活跃提案，请先归档或删除提案，或用 --force 强制删除")
    
    # 软删除：直接从列表移除（也可用 status=deleted 标记）
    projects = [x for x in projects if x['id'] != args.id]
    write_csv(PROJECTS_CSV, headers, projects)
    
    # 同时更新 mapping
    _, mappings = load_mapping()
    mappings = [m for m in mappings if m['project_id'] != args.id]
    if mappings:
        write_csv(MAPPING_CSV, ['project_id', 'project_name', 'project_git_repo', 'proposal_id', 'proposal_name', 'proposal_status'], mappings)
    
    log(f"删除项目: {args.id}")


# ==================== 提案操作 ====================

def generate_proposal_id(proposals):
    """生成下一个提案ID: P-YYYYMMDD-XXX"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"P-{today}-"
    max_num = 0
    for p in proposals:
        if p['id'].startswith(prefix):
            try:
                num = int(p['id'].split('-')[-1])
                max_num = max(max_num, num)
            except:
                pass
    return f"{prefix}{max_num + 1:03d}"


def update_project_proposal_count(project_id):
    """更新项目的提案数量"""
    headers, projects = load_projects()
    for p in projects:
        if p['id'] == project_id:
            _, proposals = load_proposals()
            count = sum(1 for pr in proposals if pr['project_id'] == project_id and pr.get('status') != 'archived')
            p['proposal_count'] = str(count)
            break
    write_csv(PROJECTS_CSV, headers, projects)


def cmd_add_proposal(args):
    """新增提案"""
    headers, proposals = load_proposals()
    _, projects = load_projects()
    
    # 生成ID（如果未指定）
    proposal_id = args.id
    if not proposal_id:
        proposal_id = generate_proposal_id(proposals)
        log(f"自动生成提案ID: {proposal_id}")
    
    # 校验项目存在
    validate_project_exists(args.project_id, projects)
    project = get_project_by_id(args.project_id, projects)
    
    data = {
        'id': proposal_id,
        'title': args.title,
        'owner': args.owner or '',
        'status': args.status or 'intake',
        'project_id': args.project_id,
        'project_name': project['name'],
        'stage': args.stage or 'proposal',
        'prd_path': '',
        'tech_solution_path': '',
        'project_path': '',
        'git_repo': args.git_repo or project.get('git_repo', ''),
        'deployment_url': '',
        'prd_confirmation': '',
        'tech_expectations': '',
        'acceptance': '',
        'last_update': datetime.now().strftime('%Y-%m-%d'),
        'engine': args.engine or '',
        'target': args.target or '',
        'game_type': args.game_type or '',
        'notes': '',
    }
    
    # 校验数据
    validate_proposal_data(data)
    
    # 检查ID重复
    for p in proposals:
        if p['id'] == proposal_id:
            die(f"提案ID已存在: {proposal_id}")
    
    # 写入
    if not headers:
        headers = ['id', 'title', 'owner', 'status', 'project_id', 'project_name', 'stage',
                   'prd_path', 'tech_solution_path', 'project_path', 'git_repo', 'deployment_url',
                   'prd_confirmation', 'tech_expectations', 'acceptance', 'last_update',
                   'engine', 'target', 'game_type', 'notes']
    
    proposals.append(data)
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    # 更新 mapping
    mapping_headers, mappings = load_mapping()
    mapping_headers = mapping_headers or ['project_id', 'project_name', 'project_git_repo', 'proposal_id', 'proposal_name', 'proposal_status']
    mappings.append({
        'project_id': args.project_id,
        'project_name': project['name'],
        'project_git_repo': project.get('git_repo', ''),
        'proposal_id': proposal_id,
        'proposal_name': args.title,
        'proposal_status': args.status or 'intake',
    })
    write_csv(MAPPING_CSV, mapping_headers, mappings)
    
    # 更新项目的提案数量
    update_project_proposal_count(args.project_id)
    
    log(f"新增提案成功: {proposal_id} - {args.title}")
    print(proposal_id)


def cmd_list_proposals(args):
    """列出提案"""
    headers, proposals = load_proposals()
    
    if not proposals:
        log("暂无提案")
        return
    
    # 按状态过滤
    if args.status:
        proposals = [p for p in proposals if p.get('status') == args.status]
    
    if args.project_id:
        proposals = [p for p in proposals if p.get('project_id') == args.project_id]
    
    if args.project:
        proposals = [p for p in proposals if args.project.lower() in p.get('project_name', '').lower()]
    
    # 确定输出字段
    fields = args.fields.split(',') if args.fields else None
    if fields:
        fields = [f for f in fields if f in headers]
    
    if not fields:
        # 默认显示关键字段
        default_fields = ['id', 'title', 'status', 'project_name', 'owner', 'last_update']
        fields = [f for f in default_fields if f in headers]
    
    # 打印表头
    print('\t'.join(fields))
    
    # 打印数据
    for p in proposals:
        row = [p.get(f, '') for f in fields]
        print('\t'.join(row))


def cmd_get_proposal(args):
    """获取单个提案"""
    _, proposals = load_proposals()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"提案不存在: {args.id}")
    
    if args.json:
        import json
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        for k, v in p.items():
            print(f"{k}: {v}")


def cmd_update_proposal(args):
    """更新提案"""
    headers, proposals = load_proposals()
    _, projects = load_projects()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"提案不存在: {args.id}")
    
    old_project_id = p['project_id']
    
    # 可更新的字段
    if args.title is not None:
        if not args.title:
            raise ValueError("title 不能为空")
        p['title'] = args.title
    
    if args.status is not None:
        validate_enum(args.status, 'status', VALID_PROPOSAL_STATUSES)
        p['status'] = args.status
    
    if args.owner is not None:
        p['owner'] = args.owner
    
    if args.project_id is not None:
        validate_project_exists(args.project_id, projects)
        p['project_id'] = args.project_id
        project = get_project_by_id(args.project_id, projects)
        p['project_name'] = project['name']
        p['git_repo'] = project.get('git_repo', '')
    
    if args.prd_path is not None:
        p['prd_path'] = args.prd_path
    
    if args.tech_solution_path is not None:
        p['tech_solution_path'] = args.tech_solution_path
    
    if args.project_path is not None:
        p['project_path'] = args.project_path
    
    if args.git_repo is not None:
        if args.git_repo:
            validate_url_or_empty(args.git_repo, 'git_repo')
        p['git_repo'] = args.git_repo
    
    if args.deployment_url is not None:
        if args.deployment_url:
            validate_url_or_empty(args.deployment_url, 'deployment_url')
        p['deployment_url'] = args.deployment_url
    
    if args.prd_confirmation is not None:
        if args.prd_confirmation:
            validate_enum(args.prd_confirmation, 'prd_confirmation', VALID_PRDS)
        p['prd_confirmation'] = args.prd_confirmation
    
    if args.tech_expectations is not None:
        if args.tech_expectations:
            validate_enum(args.tech_expectations, 'tech_expectations', VALID_TECH_EXPS)
        p['tech_expectations'] = args.tech_expectations
    
    if args.acceptance is not None:
        if args.acceptance:
            validate_enum(args.acceptance, 'acceptance', VALID_ACCEPTANCES)
        p['acceptance'] = args.acceptance
    
    if args.stage is not None:
        validate_enum(args.stage, 'stage', VALID_PROPOSAL_STAGES)
        p['stage'] = args.stage
    
    if args.engine is not None:
        p['engine'] = args.engine
    
    if args.target is not None:
        p['target'] = args.target
    
    if args.game_type is not None:
        if args.game_type:
            validate_enum(args.game_type, 'game_type', VALID_GAME_TYPES)
        p['game_type'] = args.game_type
    
    if args.notes is not None:
        p['notes'] = args.notes
    
    # 更新最后更新时间
    p['last_update'] = datetime.now().strftime('%Y-%m-%d')
    
    # 重新校验（部分）
    validate_proposal_data(p, is_new=False)
    
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    # 更新 mapping（如果项目变了）
    if args.project_id and args.project_id != old_project_id:
        mapping_headers, mappings = load_mapping()
        for m in mappings:
            if m['proposal_id'] == args.id:
                m['project_id'] = args.project_id
                m['project_name'] = get_project_by_id(args.project_id, projects)['name']
                m['proposal_status'] = p['status']
        if mapping_headers:
            write_csv(MAPPING_CSV, mapping_headers, mappings)
        # 更新新旧项目的提案数量
        update_project_proposal_count(old_project_id)
        update_project_proposal_count(args.project_id)
    else:
        # 只更新 mapping 中该提案的状态
        mapping_headers, mappings = load_mapping()
        for m in mappings:
            if m['proposal_id'] == args.id:
                m['proposal_status'] = p['status']
        if mapping_headers:
            write_csv(MAPPING_CSV, mapping_headers, mappings)
    
    log(f"更新提案成功: {args.id}")


def cmd_delete_proposal(args):
    """删除提案"""
    headers, proposals = load_proposals()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"提案不存在: {args.id}")
    
    project_id = p['project_id']
    
    # 软删除：直接从列表移除
    proposals = [x for x in proposals if x['id'] != args.id]
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    # 从 mapping 移除
    _, mappings = load_mapping()
    mappings = [m for m in mappings if m['proposal_id'] != args.id]
    if mappings:
        write_csv(MAPPING_CSV, ['project_id', 'project_name', 'project_git_repo', 'proposal_id', 'proposal_name', 'proposal_status'], mappings)
    
    # 更新项目提案数量
    update_project_proposal_count(project_id)
    
    log(f"删除提案: {args.id}")


def cmd_archive_proposal(args):
    """归档提案（软删除）"""
    headers, proposals = load_proposals()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"提案不存在: {args.id}")
    
    p['status'] = 'archived'
    p['last_update'] = datetime.now().strftime('%Y-%m-%d')
    
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    # 更新 mapping
    _, mappings = load_mapping()
    for m in mappings:
        if m['proposal_id'] == args.id:
            m['proposal_status'] = 'archived'
    write_csv(MAPPING_CSV, ['project_id', 'project_name', 'project_git_repo', 'proposal_id', 'proposal_name', 'proposal_status'], mappings)
    
    log(f"归档提案: {args.id}")


# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(description='提案系统数据管理 CLI')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # ----- 项目子命令 -----
    proj_parser = subparsers.add_parser('project', help='项目管理')
    proj_sub = proj_parser.add_subparsers(dest='subcommand')
    
    p_add = proj_sub.add_parser('add', help='新增项目')
    p_add.add_argument('--id', help='项目ID（不指定则自动生成）')
    p_add.add_argument('--name', '--name', dest='name', required=True, help='项目名称')
    p_add.add_argument('--git-repo', dest='git_repo', help='Git仓库地址')
    p_add.set_defaults(func=cmd_add_project)
    
    p_list = proj_sub.add_parser('list', help='列出项目')
    p_list.add_argument('--fields', help='输出字段，逗号分隔')
    p_list.set_defaults(func=cmd_list_projects)
    
    p_get = proj_sub.add_parser('get', help='获取单个项目')
    p_get.add_argument('id', help='项目ID')
    p_get.add_argument('--json', action='store_true', help='JSON格式输出')
    p_get.set_defaults(func=cmd_get_project)
    
    p_update = proj_sub.add_parser('update', help='更新项目')
    p_update.add_argument('id', help='项目ID')
    p_update.add_argument('--name', help='项目名称')
    p_update.add_argument('--git-repo', dest='git_repo', help='Git仓库地址')
    p_update.set_defaults(func=cmd_update_project)
    
    p_del = proj_sub.add_parser('delete', help='删除项目')
    p_del.add_argument('id', help='项目ID')
    p_del.add_argument('--force', action='store_true', help='强制删除（有活跃提案也删除）')
    p_del.set_defaults(func=cmd_delete_project)
    
    # ----- 提案子命令 -----
    prop_parser = subparsers.add_parser('proposal', help='提案管理')
    prop_sub = prop_parser.add_subparsers(dest='subcommand')
    
    pr_add = prop_sub.add_parser('add', help='新增提案')
    pr_add.add_argument('--id', help='提案ID（不指定则自动生成）')
    pr_add.add_argument('--title', '-t', required=True, help='提案标题')
    pr_add.add_argument('--project-id', '--project-id', dest='project_id', required=True, help='所属项目ID')
    pr_add.add_argument('--owner', '-o', help='负责人')
    pr_add.add_argument('--status', '-s', default='intake', help='状态（默认intake）')
    pr_add.add_argument('--stage', default='proposal', help='阶段')
    pr_add.add_argument('--git-repo', dest='git_repo', help='Git仓库地址（覆盖项目默认值）')
    pr_add.add_argument('--engine', help='引擎')
    pr_add.add_argument('--target', help='目标平台')
    pr_add.add_argument('--game-type', dest='game_type', help='游戏类型')
    pr_add.set_defaults(func=cmd_add_proposal)
    
    pr_list = prop_sub.add_parser('list', help='列出提案')
    pr_list.add_argument('--project-id', dest='project_id', help='按项目ID过滤')
    pr_list.add_argument('--project', help='按项目名称关键词过滤')
    pr_list.add_argument('--status', '-s', help='按状态过滤')
    pr_list.add_argument('--fields', help='输出字段，逗号分隔')
    pr_list.set_defaults(func=cmd_list_proposals)
    
    pr_get = prop_sub.add_parser('get', help='获取单个提案')
    pr_get.add_argument('id', help='提案ID')
    pr_get.add_argument('--json', action='store_true', help='JSON格式输出')
    pr_get.set_defaults(func=cmd_get_proposal)
    
    pr_update = prop_sub.add_parser('update', help='更新提案')
    pr_update.add_argument('id', help='提案ID')
    pr_update.add_argument('--title', help='提案标题')
    pr_update.add_argument('--status', '-s', help='状态')
    pr_update.add_argument('--owner', '-o', help='负责人')
    pr_update.add_argument('--project-id', dest='project_id', help='所属项目ID')
    pr_update.add_argument('--prd-path', dest='prd_path', help='PRD路径')
    pr_update.add_argument('--tech-solution-path', dest='tech_solution_path', help='技术方案路径')
    pr_update.add_argument('--project-path', dest='project_path', help='项目路径')
    pr_update.add_argument('--git-repo', dest='git_repo', help='Git仓库地址')
    pr_update.add_argument('--deployment-url', dest='deployment_url', help='部署URL')
    pr_update.add_argument('--prd-confirmation', dest='prd_confirmation', help='PRD确认状态')
    pr_update.add_argument('--tech-expectations', dest='tech_expectations', help='技术期望状态')
    pr_update.add_argument('--acceptance', help='验收状态')
    pr_update.add_argument('--stage', help='阶段')
    pr_update.add_argument('--engine', help='引擎')
    pr_update.add_argument('--target', help='目标平台')
    pr_update.add_argument('--game-type', dest='game_type', help='游戏类型')
    pr_update.add_argument('--notes', help='备注')
    pr_update.set_defaults(func=cmd_update_proposal)
    
    pr_del = prop_sub.add_parser('delete', help='删除提案')
    pr_del.add_argument('id', help='提案ID')
    pr_del.set_defaults(func=cmd_delete_proposal)
    
    pr_archive = prop_sub.add_parser('archive', help='归档提案')
    pr_archive.add_argument('id', help='提案ID')
    pr_archive.set_defaults(func=cmd_archive_proposal)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if hasattr(args, 'func'):
        try:
            args.func(args)
        except ValueError as e:
            die(str(e))
        except Exception as e:
            die(f"操作失败: {e}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
