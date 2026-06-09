#!/usr/bin/env python3
"""
Pull Proposal Data from GitHub and Convert to Local CSV

Data Flow:
  GitHub master: data/proposals.json -> Convert -> Local CSV files

GitHub data/proposals.json structure:
  {
    "version": 2,
    "projects": [{
      "id": "PRJ-xxx",
      "name": "project-name",
      "description": "...",
      "gitRepo": "",
      "localPath": "",
      "createdAt": "YYYY-MM-DD",
      "updatedAt": "YYYY-MM-DD",
      "proposals": [{
        "id": "P-YYYYMMDD-XXX",
        "name": "proposal-name",
        "description": "...",
        "type": "web|app|package",
        "status": "active|in_dev|archived",
        "gitRepo": "",
        "deploymentUrl": "",
        "prdConfirmation": "",
        "techExpectations": "",
        "acceptance": "",
        "createdAt": "YYYY-MM-DD",
        "updatedAt": "YYYY-MM-DD"
      }]
    }]
  }

Local CSV output:
  - proposals.csv: flattened proposal list with project_id, project_name
  - projects.csv: project list
"""

import csv
import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error
import base64

# Configuration
PROPOSALS_ROOT = Path("/home/hermes/proposals")
LOCAL_PROJECTS_CSV = PROPOSALS_ROOT / "projects.csv"
LOCAL_PROPOSALS_CSV = PROPOSALS_ROOT / "proposals.csv"

# GitHub configuration
GITHUB_OWNER = "YeLuo45"
GITHUB_REPO = "prj-proposals-manager"
GITHUB_BRANCH = "master"
GITHUB_API_BASE = "https://api.github.com"
PROPOSALS_JSON_PATH = "data/proposals.json"


def log(msg):
    print(f"[pull-from-github] {msg}", file=sys.stderr)


def die(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)


def get_github_headers():
    token = os.environ.get('GITHUB_TOKEN', '')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'proposal-pull-script'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    return headers


def github_api_get(path):
    """GET request to GitHub API"""
    url = f"{GITHUB_API_BASE}{path}"
    req = urllib.request.Request(url, headers=get_github_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def get_file_sha(path):
    """Get SHA of a file on GitHub"""
    api_path = f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"
    data = github_api_get(api_path)
    return data.get('sha') if data else None


def get_file_content(path):
    """Get file content from GitHub (returns decoded content or None)"""
    api_path = f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"
    data = github_api_get(api_path)
    if not data or 'content' not in data:
        return None
    return base64.b64decode(data['content']).decode('utf-8')


def backup_local_csv(csv_path):
    """Create timestamped backup of local CSV before overwriting"""
    if csv_path.exists():
        backup_path = csv_path.with_suffix(f'.csv.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        content = csv_path.read_text(encoding='utf-8')
        backup_path.write_text(content, encoding='utf-8')
        log(f"Backed up {csv_path.name} -> {backup_path.name}")
        return backup_path
    return None


def write_csv(path, headers, rows):
    """Write CSV file from headers and rows"""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    log(f"Wrote {path.name}: {len(rows)} rows")


def pull_and_convert():
    """Pull proposals.json from GitHub and convert to local CSV files"""
    log(f"Pulling from {GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}")
    
    # Get proposals.json from GitHub
    content = get_file_content(PROPOSALS_JSON_PATH)
    if not content:
        die(f"Failed to get {PROPOSALS_JSON_PATH} from GitHub")
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        die(f"Invalid JSON: {e}")
    
    projects = data.get('projects', [])
    log(f"Found {len(projects)} projects on GitHub")
    
    # Backup existing local CSV files
    for csv_path in [LOCAL_PROJECTS_CSV, LOCAL_PROPOSALS_CSV]:
        backup_local_csv(csv_path)
    
    # Convert to CSV format
    project_rows = []
    proposal_rows = []
    
    for proj in projects:
        proj_id = proj.get('id', '')
        proj_name = proj.get('name', '')
        proj_description = proj.get('description', '')
        proj_git_repo = proj.get('gitRepo', '')
        proj_local_path = proj.get('localPath', '')
        proj_created = proj.get('createdAt', '')
        proj_updated = proj.get('updatedAt', '')
        proposals = proj.get('proposals', [])
        
        # Project row
        project_rows.append({
            'id': proj_id,
            'name': proj_name,
            'proposal_count': len(proposals),
            'git_repo': proj_git_repo,
            'local_path': proj_local_path,
            'prj_url': proj_local_path,
            'description': proj_description,
            'last_update': proj_updated or proj_created
        })
        
        # Proposal rows and mapping
        for prop in proposals:
            prop_id = prop.get('id', '')
            prop_name = prop.get('name', '')
            prop_status = prop.get('status', 'intake')
            prop_type = prop.get('type', 'web')
            prop_desc = prop.get('description', '')
            prop_git_repo = prop.get('gitRepo', '')
            prop_deployment_url = prop.get('prjUrl', prop.get('deploymentUrl', ''))
            prop_created = prop.get('createdAt', '')
            prop_updated = prop.get('updatedAt', '')
            prd_conf = prop.get('prdConfirmation', '')
            tech_exp = prop.get('techExpectations', '')
            acceptance = prop.get('acceptance', '')
            
            proposal_rows.append({
                'id': prop_id,
                'title': prop_name,
                'owner': '',  # Not in GitHub JSON
                'status': prop_status,
                'project_id': proj_id,
                'project_name': proj_name,
                'stage': prop_type,
                'prd_path': '',
                'tech_solution_path': '',
                'project_path': proj_local_path,
                'git_repo': prop_git_repo,
                'prj_url': prop_deployment_url,
                'deployment_branch': '',
                'prd_confirmation': prd_conf,
                'tech_expectations': tech_exp,
                'acceptance': acceptance,
                'research_direction': '',
                'last_update': prop_updated or prop_created,
                'engine': '',
                'target': '',
                'game_type': '',
                'notes': ''
            })
    
    # Write CSV files
    project_headers = ['id', 'name', 'proposal_count', 'git_repo', 'local_path', 'prj_url', 'description', 'last_update']
    write_csv(LOCAL_PROJECTS_CSV, project_headers, project_rows)
    
    proposal_headers = ['id', 'title', 'owner', 'status', 'project_id', 'project_name', 'stage',
                       'prd_path', 'tech_solution_path', 'project_path', 'git_repo', 'prj_url',
                       'deployment_branch', 'prd_confirmation', 'tech_expectations', 'acceptance',
                       'research_direction', 'last_update', 'engine', 'target', 'game_type', 'notes']
    write_csv(LOCAL_PROPOSALS_CSV, proposal_headers, proposal_rows)
    
    log(f"Conversion complete: {len(project_rows)} projects, {len(proposal_rows)} proposals")


def main():
    parser = argparse.ArgumentParser(
        description='Pull proposal data from GitHub and convert to local CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pull from GitHub and update local CSV
  python3 scripts/pull-proposals-from-github.py

  # Dry run (show what would be pulled without writing)
  python3 scripts/pull-proposals-from-github.py --dry-run

  # With custom GitHub token
  GITHUB_TOKEN=xxx python3 scripts/pull-proposals-from-github.py
"""
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be pulled without writing to local files')
    
    args = parser.parse_args()
    
    if not os.environ.get('GITHUB_TOKEN'):
        log("WARNING: GITHUB_TOKEN not set, API rate limits may apply")
    
    if args.dry_run:
        content = get_file_content(PROPOSALS_JSON_PATH)
        if content:
            data = json.loads(content)
            projects = data.get('projects', [])
            total_proposals = sum(len(p.get('proposals', [])) for p in projects)
            log(f"DRY RUN: Would pull {len(projects)} projects, {total_proposals} proposals")
            for p in projects[:3]:
                log(f"  - {p.get('id')}: {p.get('name')} ({len(p.get('proposals', []))} proposals)")
            if len(projects) > 3:
                log(f"  ... and {len(projects) - 3} more projects")
        else:
            log(f"DRY RUN: {PROPOSALS_JSON_PATH} not found on GitHub")
    else:
        pull_and_convert()
        log("Run sync-proposals-to-website.py to push local changes back to GitHub if needed")


if __name__ == '__main__':
    main()
