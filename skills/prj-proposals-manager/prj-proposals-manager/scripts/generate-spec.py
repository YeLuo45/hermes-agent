#!/usr/bin/env python3
"""
Generate OpenSpec-style SPEC files from accepted proposals or initialize from existing projects.

Two modes:
1. From proposal: Reads PRD and technical solution from workspace-pm/proposals/{project_id}/,
   generates OpenSpec-compliant spec files to workspace-dev/proposals/{project_name}/SPEC/
2. Init mode: Initializes SPEC for existing projects without proposals,
   reading from README.md, existing SPEC.md, or projects.csv description

OpenSpec schema: https://github.com/YeLuo45/OpenSpec
Templates sourced from schemas/spec-driven/templates/

Usage:
    # Generate SPEC from accepted proposal
    python3 scripts/generate-spec.py <project_id>

    # Initialize SPEC for existing project (no proposal)
    python3 scripts/generate-spec.py --init <project_id>
    python3 scripts/generate-spec.py --init todolist --name "Todo List App"
    python3 scripts/generate-spec.py --init --all           # init all projects without SPEC
    python3 scripts/generate-spec.py --init --all --dry-run # preview all

    # Dry run
    python3 scripts/generate-spec.py <project_id> --dry-run
    python3 scripts/generate-spec.py --init <project_id> --dry-run
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path


PROPOSALS_ROOT = Path('/home/hermes/.hermes/proposals')
PM_PROPOSALS = PROPOSALS_ROOT / 'workspace-pm' / 'proposals'
DEV_PROPOSALS = PROPOSALS_ROOT / 'workspace-dev' / 'proposals'
PROJECTS_CSV = PROPOSALS_ROOT / 'projects.csv'


def load_project_map():
    """Load project_id -> project_name mapping."""
    mapping = {}
    with open(PROJECTS_CSV) as f:
        for row in csv.DictReader(f):
            mapping[row['id']] = row['name']
    return mapping


def find_prd_tech_files(pm_project_path):
    """Find PRD and technical solution files in a PM project directory."""
    if not pm_project_path.is_dir():
        return None, None

    prd_files = []
    tech_files = []

    for f in sorted(pm_project_path.iterdir()):
        if not f.is_file() or not f.suffix == '.md':
            continue
        name_lower = f.stem.lower()
        if 'prd' in name_lower or f.stem.startswith('P-') and '-prd' in name_lower:
            prd_files.append(f)
        elif 'tech' in name_lower or 'solution' in name_lower or 'technical' in name_lower:
            tech_files.append(f)

    # Return latest PRD and tech file
    latest_prd = prd_files[-1] if prd_files else None
    latest_tech = tech_files[-1] if tech_files else None
    return latest_prd, latest_tech


def read_file_content(filepath):
    """Read file content, returns empty string if file doesn't exist."""
    if not filepath or not filepath.exists():
        return ''
    return filepath.read_text(errors='replace')


def extract_sections(content):
    """Extract structured sections from PRD/tech doc content."""
    sections = {}
    current_title = 'intro'
    current_content = []

    for line in content.split('\n'):
        line = line.rstrip()
        # Match markdown headers (## or ###)
        m = re.match(r'^(#{2,3})\s+(.+)$', line)
        if m:
            if current_content or current_title == 'intro':
                sections[current_title] = '\n'.join(current_content).strip()
            current_title = m.group(2).strip().lower().replace(' ', '_')
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_title] = '\n'.join(current_content).strip()

    return sections


def generate_proposal_md(sections, project_name):
    """Generate OpenSpec proposal.md from PRD sections."""
    why = sections.get('why', sections.get('背景', sections.get('problem', '')))
    what = sections.get('what', sections.get('功能描述', sections.get('功能', '')))
    capabilities_new = sections.get('new_capabilities', sections.get('新增功能', sections.get('功能列表', '')))
    impact = sections.get('impact', sections.get('影响范围', sections.get('影响', '')))

    # Fallback: extract from intro or first non-empty section
    if not why and 'intro' in sections:
        why = sections['intro'][:500]

    return f"""## Why

<!-- Explain the motivation for this change. What problem does this solve? Why now? -->

{why if why else f'{project_name} - 需要实现的功能改进'}

## What Changes

<!-- Describe what will change. Be specific about new capabilities, modifications, or removals. -->

{what if what else '功能详情见 PRD 文档'}

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md -->

{capabilities_new if capabilities_new else '- `<feature>`: 功能描述'}

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->

-

## Impact

<!-- Affected code, APIs, dependencies, systems -->

{impact if impact else '详见技术方案'}
"""


def generate_spec_md(sections):
    """Generate OpenSpec spec.md (requirements with GHERKIN scenarios) from PRD."""
    requirements = sections.get('requirements', sections.get('功能需求', sections.get('需求', '')))
    scenarios = sections.get('scenarios', sections.get('场景', sections.get('test_cases', '')))

    if not requirements and 'intro' in sections:
        req_text = sections['intro']
    else:
        req_text = requirements if requirements else '功能需求详见 PRD 文档'

    return f"""## ADDED Requirements

### Requirement: <!-- requirement name -->
<!-- requirement text -->

{req_text}

#### Scenario: <!-- scenario name -->
- **WHEN** <!-- condition -->
- **THEN** <!-- expected outcome -->

{scenarios if scenarios else ''}
"""


def generate_design_md(sections, tech_sections):
    """Generate OpenSpec design.md from technical solution."""
    context = tech_sections.get('context', tech_sections.get('背景', ''))
    goals = tech_sections.get('goals', tech_sections.get('目标', ''))
    decisions = tech_sections.get('decisions', tech_sections.get('设计决策', tech_sections.get('架构', '')))
    risks = tech_sections.get('risks', tech_sections.get('风险', ''))

    # Fallback to tech solution content
    if not context and tech_sections:
        context = list(tech_sections.values())[0][:1000] if tech_sections else ''

    goals_default = '- 实现功能需求\n- 保证代码质量\n- 便于维护扩展'
    return f"""## Context

<!-- Background and current state -->

{context if context else '技术方案详情见 tech-solution 文档'}

## Goals / Non-Goals

**Goals:**
<!-- What this design aims to achieve -->

{goals if goals else goals_default}

**Non-Goals:**
<!-- What is explicitly out of scope -->

-

## Decisions

<!-- Key design decisions and rationale -->

{decisions if decisions else '技术方案待补充'}

## Risks / Trade-offs

<!-- Known risks and trade-offs -->

{risks if risks else '暂无已知风险'}
"""


def generate_tasks_md(sections, tech_sections):
    """Generate OpenSpec tasks.md checklist from technical solution."""
    tasks = tech_sections.get('tasks', tech_sections.get('任务列表', tech_sections.get('implementation', '')))

    if not tasks and tech_sections:
        # Try to extract from first non-empty section
        for v in tech_sections.values():
            if len(v) > 100:
                tasks = v
                break

    if not tasks:
        checkbox = '- [ ]'
        tasks = f'{checkbox} 1.1 实现核心功能\n{checkbox} 1.2 编写单元测试\n{checkbox} 2.1 集成测试\n{checkbox} 2.2 部署上线'

    return f"""## 1. <!-- Task Group Name -->

{tasks}

## 2. <!-- Task Group Name -->

- [ ] 2.1 <!-- Task description -->
- [ ] 2.2 <!-- Task description -->
"""


def generate_openspec_yaml(project_id, project_name):
    """Generate .openspec.yaml metadata file."""
    return f"""schema: spec-driven
created: {datetime.now().strftime('%Y-%m-%d')}
project: {project_name}
proposal: {project_id}
"""


def generate_spec(project_id, dry_run=False):
    """Generate OpenSpec-style SPEC files for a project."""
    project_map = load_project_map()
    project_name = project_map.get(project_id)

    if not project_name:
        print(f"[ERROR] Unknown project_id: {project_id}")
        print(f"  Available: {', '.join(sorted(project_map.keys())[:10])}...")
        sys.exit(1)

    pm_path = PM_PROPOSALS / project_id
    if not pm_path.is_dir():
        print(f"[ERROR] PM directory not found: {pm_path}")
        sys.exit(1)

    prd_file, tech_file = find_prd_tech_files(pm_path)

    if not prd_file:
        print(f"[WARN] No PRD file found in {pm_path}")
        print(f"  Found: {[f.name for f in pm_path.iterdir() if f.is_file() and f.suffix == '.md']}")

    prd_content = read_file_content(prd_file)
    tech_content = read_file_content(tech_file)

    prd_sections = extract_sections(prd_content) if prd_content else {}
    tech_sections = extract_sections(tech_content) if tech_content else {}

    # Determine dev target directory
    dev_path = DEV_PROPOSALS / project_name
    spec_path = dev_path / 'SPEC'

    print(f"\n[GENERATE] OpenSpec SPEC for {project_id} ({project_name})")
    print(f"  PRD: {prd_file.name if prd_file else 'NOT FOUND'}")
    print(f"  Tech: {tech_file.name if tech_file else 'NOT FOUND'}")
    print(f"  Output: {spec_path}")

    if dry_run:
        print("\n[DRY-RUN] Would generate:")
        print("  - SPEC/proposal.md")
        print("  - SPEC/spec.md")
        print("  - SPEC/design.md")
        print("  - SPEC/tasks.md")
        print("  - SPEC/.openspec.yaml")
        return

    # Create SPEC directory (handle symlink)
    if dev_path.is_symlink():
        real_path = dev_path.resolve()
        print(f"[WARN] Dev path is symlink: {dev_path} -> {real_path}")
        spec_path = real_path / 'SPEC'

    spec_path.mkdir(parents=True, exist_ok=True)

    # Generate and write files
    files = {
        'proposal.md': generate_proposal_md(prd_sections, project_name),
        'spec.md': generate_spec_md(prd_sections),
        'design.md': generate_design_md(prd_sections, tech_sections),
        'tasks.md': generate_tasks_md(prd_sections, tech_sections),
        '.openspec.yaml': generate_openspec_yaml(project_id, project_name),
    }

    for fname, content in files.items():
        out_file = spec_path / fname
        out_file.write_text(content)
        print(f"  [WRITE] {fname}")

    print(f"\n[DONE] Generated OpenSpec SPEC at {spec_path}")


def find_dev_path(project_name):
    """Find the actual dev path for a project (handles symlinks)."""
    dev_path = DEV_PROPOSALS / project_name
    if dev_path.is_symlink():
        return dev_path.resolve()
    return dev_path


def find_existing_spec_sources(project_name, project_map):
    """Find README.md, existing SPEC.md, and other sources for init mode."""
    dev_path = find_dev_path(project_name)

    sources = {
        'readme': None,
        'existing_spec': None,
        'description': None,
    }

    # Try README.md
    readme_paths = [
        dev_path / 'README.md',
        dev_path / 'readme.md',
    ]
    for p in readme_paths:
        if p.exists() and p.is_file():
            sources['readme'] = p
            break

    # Try existing SPEC.md (in root of project)
    spec_paths = [
        dev_path / 'SPEC.md',
        dev_path / 'spec.md',
    ]
    for p in spec_paths:
        if p.exists() and p.is_file():
            sources['existing_spec'] = p
            break

    # Try project description from projects.csv
    for pid, pname in project_map.items():
        if pname == project_name:
            # Get description from CSV if available (requires loading full CSV)
            break

    return sources, dev_path


def parse_readme_for_spec(readme_path):
    """Parse README.md to extract project info for SPEC generation."""
    content = readme_path.read_text(errors='replace') if readme_path else ''

    info = {
        'name': '',
        'tagline': '',
        'description': '',
        'features': [],
        'tech_stack': [],
    }

    if not content:
        return info

    lines = content.split('\n')
    in_features = False

    for i, line in enumerate(lines):
        line = line.strip()

        # Extract project name from first heading
        if line.startswith('# ') and not info['name']:
            info['name'] = line[2:].strip()

        # Extract tagline (first line after name that isn't empty or code)
        if info['name'] and not info['tagline'] and line and not line.startswith('```'):
            if not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
                info['tagline'] = line

        # Extract features (bullet points)
        if in_features:
            if line.startswith('- '):
                info['features'].append(line[2:])
            elif line.startswith('##') or line.startswith('#'):
                in_features = False
        if 'feature' in line.lower() or '功能' in line or '特性' in line:
            in_features = True

        # Extract tech stack (code blocks with package names)
        if line.startswith('```'):
            continue
        if any(kw in line.lower() for kw in ['react', 'vue', 'angular', 'node', 'python', 'fastapi', 'django', 'flask', 'typescript', 'rust', 'go']):
            info['tech_stack'].append(line.strip())

    # Fallback description from content
    if not info['description']:
        paras = [l.strip() for l in content.split('\n\n') if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('```')]
        if paras:
            info['description'] = paras[0][:500]

    return info


def generate_init_proposal_md(info, project_name, display_name):
    """Generate proposal.md for init mode."""
    name = display_name or info.get('name', project_name)
    tagline = info.get('tagline', '') or f'{name} - 项目初始化'

    return f"""## Why

<!-- Initial project specification. Document why this project exists and what problem it solves. -->

{tagline}

## What Changes

<!-- Describe what this project does. Be specific about capabilities and scope. -->

{info.get('description', '项目初始化文档待完善')}

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Each creates specs/<name>/spec.md -->

- `{project_name}`: {info.get('description', '核心功能待定义')}

### Modified Capabilities
<!-- Existing capabilities being modified. Leave empty if new project. -->

-

## Impact

<!-- Affected code, APIs, dependencies, systems -->

- New project: {name}
- Tech stack: {', '.join(info.get('tech_stack', [])[:5]) or '待定'}
"""


def generate_init_spec_md(info, project_name):
    """Generate spec.md for init mode."""
    features = info.get('features', [])
    feature_text = '\n'.join([f'- {f}' for f in features]) if features else '- 核心功能待定义'

    return f"""## ADDED Requirements

### Requirement: <!-- requirement name -->
<!-- High-level requirement description -->

{feature_text}

#### Scenario: <!-- scenario name -->
- **WHEN** <!-- user action or condition -->
- **THEN** <!-- expected outcome -->

#### Scenario: Default flow
- **WHEN** User accesses the application
- **THEN** Application loads and displays the main interface
"""


def generate_init_design_md(info, project_name, display_name):
    """Generate design.md for init mode."""
    name = display_name or info.get('name', project_name)
    tech_stack = ', '.join(info.get('tech_stack', [])[:8]) or '待定'

    return f"""## Context

<!-- Background and current state -->

{name} - {info.get('description', '项目初始化')}

## Goals / Non-Goals

**Goals:**
- 实现核心功能需求
- 保证代码质量和可维护性
- 提供良好的用户体验

**Non-Goals:**
- 高级功能和优化暂不考虑
- 多平台适配暂不考虑

## Decisions

<!-- Key design decisions and rationale -->

- 技术栈: {tech_stack}
- 架构模式: 待技术方案确定

## Risks / Trade-offs

<!-- Known risks and trade-offs -->

- 项目初期架构设计可能需要调整
"""


def generate_init_tasks_md():
    """Generate tasks.md for init mode."""
    return """## 1. 项目初始化

- [ ] 1.1 环境搭建和依赖安装
- [ ] 1.2 项目结构设计
- [ ] 1.3 基础框架搭建

## 2. 核心功能开发

- [ ] 2.1 核心功能模块开发
- [ ] 2.2 单元测试编写
- [ ] 2.3 集成测试

## 3. 部署上线

- [ ] 3.1 部署配置
- [ ] 3.2 上线验证
"""


def init_spec_for_project(project_name, display_name, dry_run=False):
    """Initialize OpenSpec SPEC for an existing project without proposals."""
    project_map = load_project_map()

    # Try to find by project_id first, then by name
    project_id = project_map.get(project_name, project_name)
    if project_id not in project_map:
        # Check if it's a project name
        for pid, pname in project_map.items():
            if pname == project_name:
                project_id = pid
                break

    sources, dev_path = find_existing_spec_sources(project_name, project_map)

    print(f"\n[INIT] OpenSpec SPEC for existing project: {project_name}")
    if display_name:
        print(f"  Display name: {display_name}")
    print(f"  Dev path: {dev_path}")
    print(f"  README: {sources['readme'].name if sources['readme'] else 'NOT FOUND'}")
    print(f"  Existing SPEC.md: {sources['existing_spec'].name if sources['existing_spec'] else 'NOT FOUND'}")

    if dry_run:
        print("\n[DRY-RUN] Would generate:")
        print("  - SPEC/proposal.md")
        print("  - SPEC/spec.md")
        print("  - SPEC/design.md")
        print("  - SPEC/tasks.md")
        print("  - SPEC/.openspec.yaml")
        return

    # Parse README if exists
    info = {'name': project_name, 'description': '', 'features': [], 'tech_stack': [], 'tagline': ''}
    if sources['readme']:
        info = parse_readme_for_spec(sources['readme'])
        info['name'] = display_name or info.get('name', project_name)
    elif display_name:
        info['name'] = display_name

    # Create SPEC directory
    spec_path = dev_path / 'SPEC'
    spec_path.mkdir(parents=True, exist_ok=True)

    # Generate files
    files = {
        'proposal.md': generate_init_proposal_md(info, project_name, display_name),
        'spec.md': generate_init_spec_md(info, project_name),
        'design.md': generate_init_design_md(info, project_name, display_name),
        'tasks.md': generate_init_tasks_md(),
        '.openspec.yaml': f"""schema: spec-driven
created: {datetime.now().strftime('%Y-%m-%d')}
project: {project_name}
init: true
""",
    }

    for fname, content in files.items():
        out_file = spec_path / fname
        out_file.write_text(content)
        print(f"  [WRITE] {fname}")

    print(f"\n[DONE] Initialized OpenSpec SPEC at {spec_path}")


def init_all_specs(dry_run=False):
    """Initialize SPEC for all projects that don't have one."""
    project_map = load_project_map()

    # Find all projects with existing SPEC directories
    existing_specs = set()
    for p in DEV_PROPOSALS.iterdir():
        if p.is_dir() and (p / 'SPEC').exists():
            existing_specs.add(p.name)

    # Find projects without SPEC
    projects_without_spec = []
    for project_name in os.listdir(DEV_PROPOSALS):
        dev_path = DEV_PROPOSALS / project_name
        if dev_path.is_dir() and project_name not in existing_specs:
            projects_without_spec.append(project_name)

    print(f"\n[INIT-ALL] Found {len(projects_without_spec)} projects without SPEC")
    print(f"  Projects: {', '.join(projects_without_spec[:10])}{'...' if len(projects_without_spec) > 10 else ''}")

    if dry_run:
        print("\n[DRY-RUN] Would initialize SPEC for:")
        for p in projects_without_spec:
            print(f"  - {p}")
        return

    for project_name in sorted(projects_without_spec):
        init_spec_for_project(project_name, None, dry_run=False)
        print()


def main():
    parser = argparse.ArgumentParser(description='Generate OpenSpec SPEC from accepted proposal or initialize for existing project')
    parser.add_argument('project_id', nargs='?', help='Project ID (e.g. PRJ-20260516-001, or project name like todolist for --init)')
    parser.add_argument('--init', action='store_true', help='Initialize SPEC for existing project (no proposal required)')
    parser.add_argument('--all', action='store_true', help='Initialize SPEC for all projects without SPEC (use with --init)')
    parser.add_argument('--name', help='Project display name (for --init mode)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be generated')

    args = parser.parse_args()

    if args.all and args.init:
        init_all_specs(args.dry_run)
    elif args.init and args.project_id:
        init_spec_for_project(args.project_id, args.name, args.dry_run)
    elif args.project_id:
        generate_spec(args.project_id, args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()