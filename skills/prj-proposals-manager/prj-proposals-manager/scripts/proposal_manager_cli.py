#!/usr/bin/env python3
"""
Proposal System Data Management CLI
All project and proposal CRUD operations must go through this script.
CSV is the source of truth; markdown files are derived from CSV.

CSV Schema:
- projects.csv: id, name, proposal_count, git_repo, local_path, description, last_update
- proposals.csv: id, title, owner, status, project_id, project_name, stage,
                 prd_path, tech_solution_path, project_path, git_repo, deployment_url,
                 deployment_branch, prd_confirmation, tech_expectations, acceptance,
                 research_direction, last_update, engine, target, game_type, notes
"""

import csv
import sys
import os
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Configuration paths
PROPOSALS_ROOT = Path("/home/hermes/.hermes/proposals")
PROJECTS_CSV = PROPOSALS_ROOT / "projects.csv"
PROPOSALS_CSV = PROPOSALS_ROOT / "proposals.csv"

# Workspace directories
DEV_OUTPUT_DIR = PROPOSALS_ROOT / "workspace-dev"
PM_OUTPUT_DIR = PROPOSALS_ROOT / "workspace-pm"
TEST_OUTPUT_DIR = PROPOSALS_ROOT / "workspace-test"
RESEARCH_OUTPUT_DIR = PROPOSALS_ROOT / "workspace-research"

# Valid enum values
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

# CSV Headers
PROJECTS_CSV_HEADERS = ['id', 'name', 'proposal_count', 'git_repo', 'local_path', 'description', 'last_update']
PROPOSALS_CSV_HEADERS = ['id', 'title', 'owner', 'status', 'project_id', 'project_name', 'stage',
                          'prd_path', 'tech_solution_path', 'project_path', 'git_repo', 'deployment_url',
                          'deployment_branch', 'prd_confirmation', 'tech_expectations', 'acceptance',
                          'research_direction', 'last_update', 'engine', 'target', 'game_type', 'notes']

# ID patterns
PROJECT_ID_PATTERN = re.compile(r'^PRJ-\d{8}-\d{3}$')
PROPOSAL_ID_PATTERN = re.compile(r'^P-\d{8}-\d{3}$')


def log(msg):
    print(f"[proposal-manager] {msg}", file=sys.stderr)


def die(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)


def read_csv(path):
    """Read CSV, return (headers, rows)"""
    if not path.exists():
        return [], []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def write_csv(path, headers, rows):
    """Write CSV preserving header order"""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def load_projects():
    headers, rows = read_csv(PROJECTS_CSV)
    return headers, rows


def load_proposals():
    headers, rows = read_csv(PROPOSALS_CSV)
    return headers, rows


# ==================== Validation ====================

def validate_project_id(project_id):
    if not PROJECT_ID_PATTERN.match(project_id):
        raise ValueError(f"Invalid project ID format: {project_id}, expected: PRJ-YYYYMMDD-XXX")


def validate_proposal_id(proposal_id):
    if not PROPOSAL_ID_PATTERN.match(proposal_id):
        raise ValueError(f"Invalid proposal ID format: {proposal_id}, expected: P-YYYYMMDD-XXX")


def validate_non_empty(value, field_name):
    if not value or not str(value).strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_enum(value, field_name, valid_values):
    if value and value not in valid_values:
        raise ValueError(f"Invalid {field_name}: {value}, valid values: {valid_values}")


def validate_url_or_empty(value, field_name):
    if value and not value.strip():
        return
    if value and not (value.startswith('http://') or value.startswith('https://') or value.startswith('git@')):
        raise ValueError(f"{field_name} must start with http://, https://, or git@")


def get_project_by_id(project_id, projects):
    for p in projects:
        if p['id'] == project_id:
            return p
    return None


def get_proposal_by_id(proposal_id, proposals):
    for p in proposals:
        if p['id'] == proposal_id:
            return p
    return None


def validate_project_exists(project_id, projects):
    if not get_project_by_id(project_id, projects):
        raise ValueError(f"Project does not exist: {project_id}")


def validate_proposal_exists(proposal_id, proposals):
    if not get_proposal_by_id(proposal_id, proposals):
        raise ValueError(f"Proposal does not exist: {proposal_id}")


# ==================== Workspace Initialization ====================

def init_project_workspace(project_id, project_name, workspace_type='dev'):
    """Initialize project workspace directory structure"""
    workspace_map = {
        'dev': DEV_OUTPUT_DIR,
        'pm': PM_OUTPUT_DIR,
        'test': TEST_OUTPUT_DIR,
        'research': RESEARCH_OUTPUT_DIR,
    }
    
    if workspace_type not in workspace_map:
        raise ValueError(f"Invalid workspace type: {workspace_type}, must be one of: {list(workspace_map.keys())}")
    
    workspace_root = workspace_map[workspace_type]
    project_dir = workspace_root / project_name / "proposals"
    docs_dir = project_dir / "docs"
    
    # Create directory structure
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create initial docs/index.md
    index_file = docs_dir / "index.md"
    if not index_file.exists():
        index_content = f"""# {project_name} - Documents Index

## Project: {project_name}
**Project ID**: {project_id}
**Created**: {datetime.now().strftime('%Y-%m-%d')}
**Workspace**: {workspace_type}

## Document Versions

### Proposal
| Version | File | Updated | Notes |
|---------|------|---------|-------|

### PRD
| Version | File | Updated | Notes |
|---------|------|---------|-------|

### Technical Solution
| Version | File | Updated | Notes |
|---------|------|---------|-------|

### Test Cases
| Version | File | Updated | Notes |
|---------|------|---------|-------|

"""
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    return str(project_dir)


# ==================== Project Operations ====================

def generate_project_id(projects):
    """Generate next project ID: PRJ-YYYYMMDD-XXX"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"PRJ-{today}-"
    max_num = 0
    for p in projects:
        if p.get('id', '').startswith(prefix):
            try:
                num = int(p['id'].split('-')[-1])
                max_num = max(max_num, num)
            except:
                pass
    return f"{prefix}{max_num + 1:03d}"


def cmd_add_project(args):
    """Add new project"""
    headers, projects = load_projects()
    
    # Generate ID if not specified
    project_id = args.id
    if not project_id:
        project_id = generate_project_id(projects)
        log(f"Auto-generated project ID: {project_id}")
    
    # Validate
    validate_project_id(project_id)
    validate_non_empty(args.name, 'name')
    
    # Check for duplicate ID
    if get_project_by_id(project_id, projects):
        die(f"Project ID already exists: {project_id}")
    
    data = {
        'id': project_id,
        'name': args.name,
        'proposal_count': '0',
        'git_repo': args.git_repo or '',
        'local_path': args.local_path or '',
        'description': args.description or '',
        'last_update': datetime.now().strftime('%Y-%m-%d'),
    }
    
    # Write
    if not headers:
        headers = PROJECTS_CSV_HEADERS
    projects.append(data)
    write_csv(PROJECTS_CSV, headers, projects)
    
    # Initialize workspace if requested
    if args.init_workspace:
        for ws_type in ['dev', 'pm', 'test', 'research']:
            init_project_workspace(project_id, args.name, ws_type)
        log(f"Initialized workspaces for: {args.name}")
    
    log(f"Added project: {project_id} - {args.name}")
    print(project_id)


def cmd_list_projects(args):
    """List projects"""
    headers, projects = load_projects()
    
    if not projects:
        log("No projects found")
        return
    
    fields = args.fields.split(',') if args.fields else headers
    fields = [f for f in fields if f in headers]
    
    print('\t'.join(fields))
    for p in projects:
        row = [p.get(f, '') for f in fields]
        print('\t'.join(row))


def cmd_get_project(args):
    """Get single project"""
    _, projects = load_projects()
    
    p = get_project_by_id(args.id, projects)
    if not p:
        die(f"Project not found: {args.id}")
    
    if args.json:
        import json
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        for k, v in p.items():
            print(f"{k}: {v}")


def cmd_update_project(args):
    """Update project"""
    headers, projects = load_projects()
    
    p = get_project_by_id(args.id, projects)
    if not p:
        die(f"Project not found: {args.id}")
    
    # All updatable fields
    update_fields = {
        'name': args.name,
        'git_repo': args.git_repo,
        'local_path': args.local_path,
        'description': args.description,
    }
    
    for field, value in update_fields.items():
        if value is not None:
            if field in ('git_repo',):
                if value:
                    validate_url_or_empty(value, field)
            elif field == 'name' and not value:
                raise ValueError("name cannot be empty")
            p[field] = value
    
    p['last_update'] = datetime.now().strftime('%Y-%m-%d')
    
    write_csv(PROJECTS_CSV, headers, projects)
    log(f"Updated project: {args.id}")


def cmd_delete_project(args):
    """Delete project (removes from CSV)"""
    headers, projects = load_projects()
    
    p = get_project_by_id(args.id, projects)
    if not p:
        die(f"Project not found: {args.id}")
    
    if not args.force:
        _, proposals = load_proposals()
        active_count = sum(1 for pr in proposals 
                          if pr.get('project_id') == args.id 
                          and pr.get('status') not in ('archived', 'deployed'))
        if active_count > 0:
            die(f"Project has {active_count} active proposals. Delete proposals first or use --force")
    
    projects = [x for x in projects if x['id'] != args.id]
    write_csv(PROJECTS_CSV, headers, projects)
    
    log(f"Deleted project: {args.id}")


def cmd_init_workspace(args):
    """Initialize project workspace"""
    _, projects = load_projects()
    
    p = get_project_by_id(args.project_id, projects)
    if not p:
        die(f"Project not found: {args.project_id}")
    
    for ws_type in args.workspace.split(','):
        ws_type = ws_type.strip()
        path = init_project_workspace(args.project_id, p['name'], ws_type)
        log(f"Initialized {ws_type} workspace: {path}")
    
    print(f"Initialized workspace(s): {args.workspace}")


# ==================== Proposal Operations ====================

def generate_proposal_id(proposals):
    """Generate next proposal ID: P-YYYYMMDD-XXX"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"P-{today}-"
    max_num = 0
    for p in proposals:
        if p.get('id', '').startswith(prefix):
            try:
                num = int(p['id'].split('-')[-1])
                max_num = max(max_num, num)
            except:
                pass
    return f"{prefix}{max_num + 1:03d}"


def update_project_proposal_count(project_id):
    """Update project's proposal count"""
    headers, projects = load_projects()
    for p in projects:
        if p['id'] == project_id:
            _, proposals = load_proposals()
            count = sum(1 for pr in proposals 
                       if pr.get('project_id') == project_id 
                       and pr.get('status') != 'archived')
            p['proposal_count'] = str(count)
            p['last_update'] = datetime.now().strftime('%Y-%m-%d')
            break
    write_csv(PROJECTS_CSV, headers, projects)


def cmd_add_proposal(args):
    """Add new proposal"""
    headers, proposals = load_proposals()
    _, projects = load_projects()
    
    # Generate ID if not specified
    proposal_id = args.id
    if not proposal_id:
        proposal_id = generate_proposal_id(proposals)
        log(f"Auto-generated proposal ID: {proposal_id}")
    
    # Validate
    validate_proposal_id(proposal_id)
    validate_non_empty(args.title, 'title')
    validate_project_exists(args.project_id, projects)
    project = get_project_by_id(args.project_id, projects)
    
    if get_proposal_by_id(proposal_id, proposals):
        die(f"Proposal ID already exists: {proposal_id}")
    
    # Determine local project path
    local_project_path = args.project_path or project.get('local_path', '')
    if not local_project_path:
        local_project_path = str(DEV_OUTPUT_DIR / project['name'] / "proposals")
    
    data = {
        'id': proposal_id,
        'title': args.title,
        'owner': args.owner or '',
        'status': args.status or 'intake',
        'project_id': args.project_id,
        'project_name': project['name'],
        'stage': args.stage or 'proposal',
        'prd_path': args.prd_path or '',
        'tech_solution_path': args.tech_solution_path or '',
        'project_path': local_project_path,
        'git_repo': args.git_repo or project.get('git_repo', ''),
        'deployment_url': args.deployment_url or '',
        'deployment_branch': args.deployment_branch or '',
        'prd_confirmation': args.prd_confirmation or '',
        'tech_expectations': args.tech_expectations or '',
        'acceptance': args.acceptance or '',
        'research_direction': args.research_direction or '',
        'last_update': datetime.now().strftime('%Y-%m-%d'),
        'engine': args.engine or '',
        'target': args.target or '',
        'game_type': args.game_type or '',
        'notes': args.notes or '',
    }
    
    # Write
    if not headers:
        headers = PROPOSALS_CSV_HEADERS
    proposals.append(data)
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    # Update project proposal count
    update_project_proposal_count(args.project_id)
    
    log(f"Added proposal: {proposal_id} - {args.title}")
    print(proposal_id)


def cmd_list_proposals(args):
    """List proposals"""
    headers, proposals = load_proposals()
    
    if not proposals:
        log("No proposals found")
        return
    
    # Apply filters
    if args.status:
        proposals = [p for p in proposals if p.get('status') == args.status]
    if args.project_id:
        proposals = [p for p in proposals if p.get('project_id') == args.project_id]
    if args.project:
        proposals = [p for p in proposals if args.project.lower() in p.get('project_name', '').lower()]
    
    # Determine output fields
    fields = args.fields.split(',') if args.fields else None
    if fields:
        fields = [f for f in fields if f in headers]
    else:
        default_fields = ['id', 'title', 'status', 'project_name', 'owner', 'last_update']
        fields = [f for f in default_fields if f in headers]
    
    print('\t'.join(fields))
    for p in proposals:
        row = [p.get(f, '') for f in fields]
        print('\t'.join(row))


def cmd_get_proposal(args):
    """Get single proposal"""
    _, proposals = load_proposals()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"Proposal not found: {args.id}")
    
    if args.json:
        import json
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        for k, v in p.items():
            print(f"{k}: {v}")


def cmd_update_proposal(args):
    """Update proposal - supports ALL CSV fields"""
    headers, proposals = load_proposals()
    _, projects = load_projects()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"Proposal not found: {args.id}")
    
    old_project_id = p['project_id']
    
    # All possible fields that can be updated
    update_specs = {
        'title': ('str', args.title),
        'owner': ('str', args.owner),
        'status': ('enum', args.status, VALID_PROPOSAL_STATUSES),
        'project_id': ('project', args.project_id),
        'stage': ('enum', args.stage, VALID_PROPOSAL_STAGES),
        'prd_path': ('str', args.prd_path),
        'tech_solution_path': ('str', args.tech_solution_path),
        'project_path': ('str', args.project_path),
        'git_repo': ('url', args.git_repo),
        'deployment_url': ('url', args.deployment_url),
        'deployment_branch': ('str', args.deployment_branch),
        'prd_confirmation': ('enum', args.prd_confirmation, VALID_PRDS),
        'tech_expectations': ('enum', args.tech_expectations, VALID_TECH_EXPS),
        'acceptance': ('enum', args.acceptance, VALID_ACCEPTANCES),
        'research_direction': ('str', args.research_direction),
        'engine': ('str', args.engine),
        'target': ('str', args.target),
        'game_type': ('enum', args.game_type, VALID_GAME_TYPES),
        'notes': ('str', args.notes),
    }
    
    for field, spec in update_specs.items():
        value = spec[1] if len(spec) == 2 else spec[2] if len(spec) == 3 else None
        # Find the actual value from args
        arg_val = getattr(args, field.replace('-', '_'), None)
        if arg_val is None:
            continue
        
        if spec[0] == 'enum':
            if arg_val:
                if spec[2] and arg_val not in spec[2]:
                    raise ValueError(f"Invalid {field}: {arg_val}, valid: {spec[2]}")
            p[field] = arg_val
        elif spec[0] == 'url':
            if arg_val:
                validate_url_or_empty(arg_val, field)
            p[field] = arg_val
        elif spec[0] == 'project':
            if arg_val:
                validate_project_exists(arg_val, projects)
                proj = get_project_by_id(arg_val, projects)
                p['project_id'] = arg_val
                p['project_name'] = proj['name']
                p['git_repo'] = proj.get('git_repo', '')
        else:
            p[field] = arg_val
    
    p['last_update'] = datetime.now().strftime('%Y-%m-%d')
    
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    # Update project proposal count if project changed
    if args.project_id and args.project_id != old_project_id:
        update_project_proposal_count(old_project_id)
        update_project_proposal_count(args.project_id)
    
    log(f"Updated proposal: {args.id}")


def cmd_delete_proposal(args):
    """Delete proposal"""
    headers, proposals = load_proposals()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"Proposal not found: {args.id}")
    
    project_id = p['project_id']
    
    proposals = [x for x in proposals if x['id'] != args.id]
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    update_project_proposal_count(project_id)
    
    log(f"Deleted proposal: {args.id}")


def cmd_archive_proposal(args):
    """Archive proposal"""
    headers, proposals = load_proposals()
    
    p = get_proposal_by_id(args.id, proposals)
    if not p:
        die(f"Proposal not found: {args.id}")
    
    p['status'] = 'archived'
    p['last_update'] = datetime.now().strftime('%Y-%m-%d')
    
    write_csv(PROPOSALS_CSV, headers, proposals)
    
    log(f"Archived proposal: {args.id}")


def cmd_next_project_id(args):
    """Generate next project ID"""
    _, projects = load_projects()
    next_id = generate_project_id(projects)
    print(next_id)


def cmd_next_proposal_id(args):
    """Generate next proposal ID for a project"""
    _, proposals = load_proposals()
    project_id = args.project_id

    # Filter proposals for this project
    project_proposals = [p for p in proposals if p.get('project_id') == project_id]

    # Generate next ID based on today's date
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"P-{today}-"
    max_num = 0
    for p in project_proposals:
        pid = p.get('id', '')
        if pid.startswith(prefix):
            try:
                num = int(pid.split('-')[-1])
                max_num = max(max_num, num)
            except:
                pass

    next_id = f"{prefix}{max_num + 1:03d}"
    print(next_id)


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(
        description='Proposal System Data Management CLI - CSV is source of truth',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # ==================== Project Commands ====================
    proj_parser = subparsers.add_parser('project', help='Project management')
    proj_sub = proj_parser.add_subparsers(dest='subcommand')
    
    # project add
    p_add = proj_sub.add_parser('add', help='Add new project')
    p_add.add_argument('--id', help='Project ID (auto-generated if not specified)')
    p_add.add_argument('--name', '-n', required=True, help='Project name')
    p_add.add_argument('--git-repo', help='Git repository URL')
    p_add.add_argument('--local-path', help='Local workspace path')
    p_add.add_argument('--description', '-d', help='Project description')
    p_add.add_argument('--init-workspace', action='store_true', help='Initialize workspace directories')
    p_add.set_defaults(func=cmd_add_project)
    
    # project list
    p_list = proj_sub.add_parser('list', help='List projects')
    p_list.add_argument('--fields', '-f', help='Output fields (comma-separated)')
    p_list.set_defaults(func=cmd_list_projects)
    
    # project get
    p_get = proj_sub.add_parser('get', help='Get project details')
    p_get.add_argument('id', help='Project ID')
    p_get.add_argument('--json', action='store_true', help='JSON output')
    p_get.set_defaults(func=cmd_get_project)
    
    # project update
    p_update = proj_sub.add_parser('update', help='Update project')
    p_update.add_argument('id', help='Project ID')
    p_update.add_argument('--name', '-n', help='Project name')
    p_update.add_argument('--git-repo', help='Git repository URL')
    p_update.add_argument('--local-path', help='Local workspace path')
    p_update.add_argument('--description', '-d', help='Project description')
    p_update.set_defaults(func=cmd_update_project)
    
    # project delete
    p_del = proj_sub.add_parser('delete', help='Delete project')
    p_del.add_argument('id', help='Project ID')
    p_del.add_argument('--force', '-f', action='store_true', help='Force delete even with active proposals')
    p_del.set_defaults(func=cmd_delete_project)
    
    # project init-workspace
    p_init = proj_sub.add_parser('init-workspace', help='Initialize project workspace')
    p_init.add_argument('project_id', help='Project ID')
    p_init.add_argument('--workspace', '-w', default='dev,pm,test,research', help='Workspace types (comma-separated)')
    p_init.set_defaults(func=cmd_init_workspace)

    # project next-id
    p_next = proj_sub.add_parser('next-id', help='Generate next project ID')
    p_next.set_defaults(func=cmd_next_project_id)

    # ==================== Proposal Commands ====================
    prop_parser = subparsers.add_parser('proposal', help='Proposal management')
    prop_sub = prop_parser.add_subparsers(dest='subcommand')
    
    # proposal add
    pr_add = prop_sub.add_parser('add', help='Add new proposal')
    pr_add.add_argument('--id', help='Proposal ID (auto-generated if not specified)')
    pr_add.add_argument('--title', '-t', required=True, help='Proposal title')
    pr_add.add_argument('--project-id', required=True, help='Project ID')
    pr_add.add_argument('--owner', '-o', help='Owner')
    pr_add.add_argument('--status', '-s', default='intake', help='Status')
    pr_add.add_argument('--stage', default='proposal', help='Stage')
    pr_add.add_argument('--prd-path', help='PRD document path')
    pr_add.add_argument('--tech-solution-path', help='Technical solution path')
    pr_add.add_argument('--project-path', help='Local project path')
    pr_add.add_argument('--git-repo', help='Git repository URL')
    pr_add.add_argument('--deployment-url', help='Deployment URL')
    pr_add.add_argument('--deployment-branch', help='Deployment branch')
    pr_add.add_argument('--prd-confirmation', help='PRD confirmation status')
    pr_add.add_argument('--tech-expectations', help='Technical expectations status')
    pr_add.add_argument('--acceptance', help='Acceptance status')
    pr_add.add_argument('--research-direction', help='Research direction')
    pr_add.add_argument('--engine', help='Engine')
    pr_add.add_argument('--target', help='Target platform')
    pr_add.add_argument('--game-type', help='Game type')
    pr_add.add_argument('--notes', help='Notes')
    pr_add.set_defaults(func=cmd_add_proposal)
    
    # proposal list
    pr_list = prop_sub.add_parser('list', help='List proposals')
    pr_list.add_argument('--project-id', help='Filter by project ID')
    pr_list.add_argument('--project', help='Filter by project name (partial match)')
    pr_list.add_argument('--status', '-s', help='Filter by status')
    pr_list.add_argument('--fields', '-f', help='Output fields (comma-separated)')
    pr_list.set_defaults(func=cmd_list_proposals)
    
    # proposal get
    pr_get = prop_sub.add_parser('get', help='Get proposal details')
    pr_get.add_argument('id', help='Proposal ID')
    pr_get.add_argument('--json', action='store_true', help='JSON output')
    pr_get.set_defaults(func=cmd_get_proposal)
    
    # proposal update
    pr_update = prop_sub.add_parser('update', help='Update proposal (all fields)')
    pr_update.add_argument('id', help='Proposal ID')
    pr_update.add_argument('--title', '-t', help='Proposal title')
    pr_update.add_argument('--owner', '-o', help='Owner')
    pr_update.add_argument('--status', '-s', help='Status')
    pr_update.add_argument('--project-id', help='Project ID')
    pr_update.add_argument('--stage', help='Stage')
    pr_update.add_argument('--prd-path', help='PRD document path')
    pr_update.add_argument('--tech-solution-path', help='Technical solution path')
    pr_update.add_argument('--project-path', help='Local project path')
    pr_update.add_argument('--git-repo', help='Git repository URL')
    pr_update.add_argument('--deployment-url', help='Deployment URL')
    pr_update.add_argument('--deployment-branch', help='Deployment branch')
    pr_update.add_argument('--prd-confirmation', help='PRD confirmation status')
    pr_update.add_argument('--tech-expectations', help='Technical expectations status')
    pr_update.add_argument('--acceptance', help='Acceptance status')
    pr_update.add_argument('--research-direction', help='Research direction')
    pr_update.add_argument('--engine', help='Engine')
    pr_update.add_argument('--target', help='Target platform')
    pr_update.add_argument('--game-type', help='Game type')
    pr_update.add_argument('--notes', help='Notes')
    pr_update.set_defaults(func=cmd_update_proposal)
    
    # proposal delete
    pr_del = prop_sub.add_parser('delete', help='Delete proposal')
    pr_del.add_argument('id', help='Proposal ID')
    pr_del.set_defaults(func=cmd_delete_proposal)
    
    # proposal archive
    pr_archive = prop_sub.add_parser('archive', help='Archive proposal')
    pr_archive.add_argument('id', help='Proposal ID')
    pr_archive.set_defaults(func=cmd_archive_proposal)

    # proposal next-id
    pr_next = prop_sub.add_parser('next-id', help='Generate next proposal ID for a project')
    pr_next.add_argument('project_id', help='Project ID (e.g. PRJ-20260516-001)')
    pr_next.set_defaults(func=cmd_next_proposal_id)

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
            die(f"Operation failed: {e}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
