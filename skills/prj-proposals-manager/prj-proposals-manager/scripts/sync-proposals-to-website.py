#!/usr/bin/env python3
"""
Proposal System Sync Script - CSV to GitHub Website

Data Flow (authoritative):
  Local CSV files (projects.csv, proposals.csv) -> GitHub

Remote GitHub data is merged INTO local CSV only when remote has new entries not in local.
The two CSV files are the SOLE source of truth.
After sync, CSV files are pushed to the GitHub repository.

CSV Schema (read-only, source of truth):
- projects.csv: id, name, proposal_count, git_repo, local_path, prj_url, description, last_update
- proposals.csv: id, title, owner, status, project_id, project_name, stage,
                 prd_path, tech_solution_path, project_path, git_repo, prj_url,
                 deployment_branch, prd_confirmation, tech_expectations, acceptance,
                 research_direction, last_update, engine, target, game_type, notes
"""

import csv
import sys
import os
import re
import json
import base64
import argparse
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

# Configuration
PROPOSALS_ROOT = Path("/home/hermes/proposals")
PROJECTS_CSV = PROPOSALS_ROOT / "projects.csv"
PROPOSALS_CSV = PROPOSALS_ROOT / "proposals.csv"

# GitHub configuration
GITHUB_OWNER = "YeLuo45"
GITHUB_REPO = "prj-proposals-manager"
GITHUB_BRANCH = "master"
WEBSITE_DATA_PATH = "data/proposals.json"
PROPOSALS_DOCS_INDEX = PROPOSALS_ROOT / "proposal-docs-index.md"
PROPOSAL_INDEX = PROPOSALS_ROOT / "proposal-index.md"

# GitHub API endpoints
GITHUB_API_BASE = "https://api.github.com"


def log(msg):
    print(f"[sync-proposals] {msg}", file=sys.stderr)


def die(msg):
    log(f"ERROR: {msg}")
    sys.exit(1)


def get_github_headers():
    token = os.environ.get('GITHUB_TOKEN', '')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'proposal-sync-script'
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


def github_api_put(path, message, content, sha=None):
    """PUT request to GitHub API (create or update file)"""
    url = f"{GITHUB_API_BASE}{path}"
    data = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode('ascii'),
        'branch': GITHUB_BRANCH,
    }
    if sha:
        data['sha'] = sha
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=get_github_headers(),
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        raise Exception(f"GitHub API error {e.code}: {error_body}")


def get_file_sha(path):
    """Get SHA of a file on GitHub"""
    api_path = f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"
    data = github_api_get(api_path)
    return data.get('sha') if data else None


# ==================== CSV Reading (Source of Truth) ====================

def read_csv(path):
    """Read CSV, return (headers, rows)"""
    if not path.exists():
        return [], []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames or [], rows


def load_projects():
    headers, rows = read_csv(PROJECTS_CSV)
    return headers, rows


def load_proposals():
    headers, rows = read_csv(PROPOSALS_CSV)
    return headers, rows


# ==================== Markdown Generation ====================

def generate_proposal_index_content(projects, proposals):
    """Generate proposal-index.md content from CSV data"""
    lines = [
        "# Proposal Index",
        "",
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Active Proposals",
        ""
    ]
    
    # Group proposals by status
    status_order = [
        'intake', 'clarifying', 'prd_pending_confirmation', 'approved_for_dev',
        'in_tdd_test', 'in_dev', 'in_test_acceptance', 'test_failed',
        'accepted', 'needs_revision', 'deployed', 'deploying',
        'research_direction_pending', 'active', 'archived'
    ]
    
    proposals_by_status = {}
    for p in proposals:
        status = p.get('status', 'unknown')
        if status not in proposals_by_status:
            proposals_by_status[status] = []
        proposals_by_status[status].append(p)
    
    for status in status_order:
        if status not in proposals_by_status:
            continue
        lines.append(f"### {status.upper().replace('_', ' ')}")
        lines.append("")
        for p in sorted(proposals_by_status[status], key=lambda x: x.get('id', '')):
            lines.append(f"#### {p['id']}: {p.get('title', 'Untitled')}")
            lines.append("")
            lines.append(f"- **Project**: {p.get('project_name', 'N/A')}")
            lines.append(f"- **Owner**: {p.get('owner', 'TBD')}")
            lines.append(f"- **Stage**: {p.get('stage', 'proposal')}")
            if p.get('prd_path'):
                lines.append(f"- **PRD**: {p['prd_path']}")
            if p.get('tech_solution_path'):
                lines.append(f"- **Tech Solution**: {p['tech_solution_path']}")
            if p.get('project_path'):
                lines.append(f"- **Project Path**: {p['project_path']}")
            if p.get('prj_url'):
                lines.append(f"- **Deployment**: {p['prj_url']}")
            lines.append(f"- **Acceptance**: {p.get('acceptance', 'pending')}")
            lines.append(f"- **Last Update**: {p.get('last_update', 'N/A')}")
            if p.get('notes'):
                lines.append(f"- **Notes**: {p['notes']}")
            lines.append("")

    return '\n'.join(lines)



def generate_project_index_content(projects):
    """Generate project-index.md content from CSV data"""
    lines = [
        "# Project Index",
        "",
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total projects: {len(projects)}",
        "",
    ]
    
    for p in sorted(projects, key=lambda x: x.get('id', '')):
        lines.append(f"### {p['id']}: {p.get('name', 'Untitled')}")
        lines.append("")
        lines.append(f"- **Git Repo**: {p.get('git_repo', 'N/A')}")
        lines.append(f"- **Local Path**: {p.get('local_path', 'N/A')}")
        lines.append(f"- **Description**: {p.get('description', 'N/A')}")
        lines.append(f"- **Proposal Count**: {p.get('proposal_count', '0')}")
        lines.append(f"- **Last Update**: {p.get('last_update', 'N/A')}")
        lines.append("")
    
    return '\n'.join(lines)


def generate_proposal_docs_index_content(projects, proposals):
    """Generate proposal-docs-index.md content from CSV data"""
    lines = [
        "# Proposal Documents Index",
        "",
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    
    for p in sorted(proposals, key=lambda x: x.get('id', '')):
        lines.append(f"## {p['id']}: {p.get('title', 'Untitled')}")
        lines.append("")
        lines.append(f"| Document | Path | Version | Updated |")
        lines.append("|----------|------|---------|---------|")
        
        # Proposal
        if p.get('project_path'):
            proj_path = p.get('project_path', '')
            lines.append(f"| Proposal | `{proj_path}/docs/proposal.md` | - | {p.get('last_update', 'N/A')} |")
        
        # PRD
        if p.get('prd_path'):
            lines.append(f"| PRD | `{p['prd_path']}` | v1.0 | N/A |")
        
        # Tech Solution
        if p.get('tech_solution_path'):
            lines.append(f"| Technical Solution | `{p['tech_solution_path']}` | v1.0 | N/A |")
        
        lines.append("")
    
    return '\n'.join(lines)


def generate_website_json(projects, proposals, mapping):
    """Generate proposals.json for website from CSV data"""
    # Build project lookup
    project_lookup = {p['id']: p for p in projects}
    
    # Build website data structure
    website_data = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'projects': [],
        'total_proposals': len(proposals),
        'total_projects': len(projects)
    }
    
    # Group proposals by project
    for proj in sorted(projects, key=lambda x: x.get('id', '')):
        proj_id = proj['id']
        proj_proposals = [p for p in proposals if p.get('project_id') == proj_id]
        
        project_entry = {
            'id': proj_id,
            'name': proj.get('name', 'Untitled'),
            'gitRepo': proj.get('git_repo', ''),
            'prjUrl': proj.get('prj_url', ''),
            'description': proj.get('description', ''),
            'proposalCount': len(proj_proposals),
            'lastUpdate': proj.get('last_update', ''),
            'proposals': []
        }
        
        for p in sorted(proj_proposals, key=lambda x: x.get('id', '')):
            proposal_entry = {
                'id': p['id'],
                'title': p.get('title', 'Untitled'),
                'owner': p.get('owner', ''),
                'status': p.get('status', 'intake'),
                'stage': p.get('stage', 'proposal'),
                'prdPath': p.get('prd_path', ''),
                'techSolutionPath': p.get('tech_solution_path', ''),
                'projectPath': p.get('project_path', ''),
                'gitRepo': p.get('git_repo', ''),
                'prjUrl': p.get('prj_url', ''),
                'deploymentBranch': p.get('deployment_branch', ''),
                'prdConfirmation': p.get('prd_confirmation', ''),
                'techExpectations': p.get('tech_expectations', ''),
                'acceptance': p.get('acceptance', ''),
                'researchDirection': p.get('research_direction', ''),
                'lastUpdate': p.get('last_update', ''),
                'engine': p.get('engine', ''),
                'target': p.get('target', ''),
                'gameType': p.get('game_type', ''),
                'notes': p.get('notes', ''),
            }
            project_entry['proposals'].append(proposal_entry)
        
        website_data['projects'].append(project_entry)
    
    return json.dumps(website_data, ensure_ascii=False, indent=2)


# ==================== CSV Push to GitHub ====================

def push_csv_to_github(csv_path, remote_path, message):
    """Push a CSV file to GitHub"""
    if not csv_path.exists():
        log(f"CSV file not found: {csv_path}, skipping")
        return
    
    content = csv_path.read_text(encoding='utf-8')
    sha = get_file_sha(remote_path)
    
    try:
        result = github_api_put(
            f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{remote_path}",
            message,
            content,
            sha
        )
        log(f"Pushed {csv_path.name} to GitHub: {result.get('commit', {}).get('sha', 'N/A')[:8]}")
    except Exception as e:
        log(f"Failed to push {csv_path.name}: {e}")
        raise


def sync_csv_to_github():
    """Push all CSV files to GitHub repository"""
    log("Pushing CSV files to GitHub...")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    csv_files = [
        (PROJECTS_CSV, f"data/projects.csv"),
        (PROPOSALS_CSV, f"data/proposals.csv"),
    ]
    
    for local_path, remote_path in csv_files:
        push_csv_to_github(
            local_path,
            remote_path,
            f"sync: update {local_path.name} ({timestamp})"
        )
    
    log("CSV files pushed to GitHub successfully")


# ==================== Main Sync Logic ====================

def sync_to_github(args):
    """Main sync operation: CSV -> GitHub website data"""
    log("Starting sync: CSV -> GitHub")
    
    # Load CSV data (source of truth)
    _, projects = load_projects()
    _, proposals = load_proposals()
    _, mapping = load_mapping()
    
    log(f"Loaded {len(projects)} projects, {len(proposals)} proposals, {len(mapping)} mapping entries")
    
    # Generate markdown files locally
    if not args.csv_only:
        # Update proposal-index.md
        proposal_index_content = generate_proposal_index_content(projects, proposals)
        PROPOSAL_INDEX.write_text(proposal_index_content, encoding='utf-8')
        log(f"Updated {PROPOSAL_INDEX}")
        
        # Update proposal-docs-index.md
        docs_index_content = generate_proposal_docs_index_content(projects, proposals)
        PROPOSALS_DOCS_INDEX.write_text(docs_index_content, encoding='utf-8')
        log(f"Updated {PROPOSALS_DOCS_INDEX}")
    
    # Generate website JSON
    website_json = generate_website_json(projects, proposals, mapping)
    json_sha = get_file_sha(WEBSITE_DATA_PATH)
    
    try:
        result = github_api_put(
            f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{WEBSITE_DATA_PATH}",
            f"sync: update proposals.json ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            website_json,
            json_sha
        )
        log(f"Updated proposals.json on GitHub: {result.get('commit', {}).get('sha', 'N/A')[:8]}")
    except Exception as e:
        log(f"Failed to update proposals.json: {e}")
        raise
    
    # Push CSV files to GitHub
    sync_csv_to_github()
    
    log("Sync completed successfully")


def main():
    parser = argparse.ArgumentParser(
        description='Sync proposal system CSV data to GitHub website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full sync (CSV -> GitHub + update markdown files)
  python3 scripts/sync-proposals-to-website.py

  # CSV only sync (push CSV to GitHub)
  python3 scripts/sync-proposals-to-website.py --csv-only

  # With custom GitHub token
  GITHUB_TOKEN=xxx python3 scripts/sync-proposals-to-website.py
"""
    )
    parser.add_argument('--csv-only', action='store_true',
                       help='Only push CSV files to GitHub, do not update JSON')
    
    args = parser.parse_args()
    
    if not os.environ.get('GITHUB_TOKEN'):
        log("WARNING: GITHUB_TOKEN not set, push operations may fail")
    
    try:
        sync_to_github(args)
    except Exception as e:
        die(f"Sync failed: {e}")


if __name__ == '__main__':
    main()
