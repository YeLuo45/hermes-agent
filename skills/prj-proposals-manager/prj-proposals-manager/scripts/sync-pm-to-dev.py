#!/usr/bin/env python3
"""
Sync PRD and technical solution files from workspace-pm to workspace-dev after acceptance.

Usage:
    python3 scripts/sync-pm-to-dev.py <project_id> [--dry-run]

Examples:
    python3 scripts/sync-pm-to-dev.py PRJ-20260516-001
    python3 scripts/sync-pm-to-dev.py PRJ-20260516-001 --dry-run
"""

import argparse
import csv
import os
import shutil
import sys
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
        return [], [], []

    prd_files = []
    tech_files = []
    test_files = []

    for f in sorted(pm_project_path.iterdir()):
        if not f.is_file() or not f.suffix == '.md':
            continue
        name_lower = f.stem.lower()
        if 'prd' in name_lower or f.stem.startswith('P-') and '-prd' in name_lower:
            prd_files.append(f)
        elif 'tech' in name_lower or 'solution' in name_lower or 'technical' in name_lower:
            tech_files.append(f)
        elif 'test' in name_lower or 'spec' in name_lower or 'test-case' in name_lower:
            test_files.append(f)

    return prd_files, tech_files, test_files


def sync_project(project_id, dry_run=False):
    """Sync PRD/tech files from PM to dev workspace for a given project."""
    project_map = load_project_map()
    project_name = project_map.get(project_id)

    if not project_name:
        print(f"[ERROR] Unknown project_id: {project_id}")
        print(f"  Available projects: {', '.join(sorted(project_map.keys())[:10])}...")
        sys.exit(1)

    pm_path = PM_PROPOSALS / project_id
    if not pm_path.is_dir():
        print(f"[ERROR] PM directory not found: {pm_path}")
        sys.exit(1)

    prd_files, tech_files, test_files = find_prd_tech_files(pm_path)

    if not prd_files and not tech_files and not test_files:
        print(f"[INFO] No PRD/tech/test files found for {project_id} ({project_name})")
        return

    # Determine dev target directory
    dev_path = DEV_PROPOSALS / project_name
    if not dev_path.exists() and not dry_run:
        print(f"[WARN] Dev directory does not exist: {dev_path}")
        print(f"  Will create it")
        dev_path.mkdir(parents=True, exist_ok=True)

    # Determine if dev_path is a symlink (external repo)
    is_symlink = dev_path.is_symlink()
    if is_symlink:
        real_path = dev_path.resolve()
        print(f"[WARN] Dev path is a symlink: {dev_path} -> {real_path}")
        print(f"  PRD/tech files will be placed inside the external repo")

    print(f"\n[SYNC] {project_id} ({project_name})")
    print(f"  Source: {pm_path}")
    print(f"  Target: {dev_path}")

    for f in prd_files:
        dest = dev_path / f.name
        action = "COPY" if not dry_run else "WOULD COPY"
        print(f"  [{action}] PRD: {f.name}")
        if not dry_run:
            shutil.copy2(f, dest)

    for f in tech_files:
        dest = dev_path / f.name
        action = "COPY" if not dry_run else "WOULD COPY"
        print(f"  [{action}] TECH: {f.name}")
        if not dry_run:
            shutil.copy2(f, dest)

    for f in test_files:
        dest = dev_path / f.name
        action = "COPY" if not dry_run else "WOULD COPY"
        print(f"  [{action}] TEST: {f.name}")
        if not dry_run:
            shutil.copy2(f, dest)

    if not dry_run:
        print(f"\n[DONE] Synced {len(prd_files)} PRD + {len(tech_files)} tech + {len(test_files)} test files")


def main():
    parser = argparse.ArgumentParser(description='Sync PRD/tech from PM to Dev workspace')
    parser.add_argument('project_id', help='Project ID (e.g. PRJ-20260516-001)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()
    sync_project(args.project_id, dry_run=args.dry_run)


if __name__ == '__main__':
    main()