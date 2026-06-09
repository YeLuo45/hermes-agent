#!/usr/bin/env python3
"""
提案系统目录初始化脚本
检测是否已初始化，若已初始化则跳过，否则创建必要的目录结构。
"""

import os
import sys
from pathlib import Path

# 硬编码路径（不依赖 Path.home()）
PROPOSALS_ROOT = Path("/home/hermes/.hermes/proposals")

# 需创建的子目录
SUBDIRS = [
    "templates",
    "workspace-dev",
    "workspace-pm",
    "workspace-test",
    "workspace-research",
]

# 需创建的 CSV 文件（带表头）
CSV_FILES = {
    "projects.csv": "id,name,proposal_count,git_repo\n",
    "proposals.csv": "id,title,owner,status,project_id,project_name,stage,prd_path,tech_solution_path,project_path,git_repo,deployment_url,prd_confirmation,tech_expectations,acceptance,last_update,engine,target,game_type,notes\n",
    "project_proposal_mapping.csv": "project_id,project_name,project_git_repo,proposal_id,proposal_name,proposal_status\n",
}

# 需创建的 markdown 索引文件
MD_FILES = {
    "project-index.md": "# 项目索引\n\n",
    "proposal-index.md": "# 提案索引\n\n",
    "proposal-docs-index.md": "# 提案文档索引\n\n",
}


def check_initialized():
    """检测是否已初始化"""
    missing = []
    for subdir in SUBDIRS:
        if not (PROPOSALS_ROOT / subdir).is_dir():
            missing.append(f"  目录缺失: {subdir}")
    for csv_file in CSV_FILES:
        csv_path = PROPOSALS_ROOT / csv_file
        if not csv_path.exists():
            missing.append(f"  文件缺失: {csv_file}")
        # 检查文件是否为空
        elif csv_path.stat().st_size == 0:
            missing.append(f"  文件为空: {csv_file}")
    for md_file in MD_FILES:
        md_path = PROPOSALS_ROOT / md_file
        if not md_path.exists():
            missing.append(f"  文件缺失: {md_file}")
    return missing


def init_dirs():
    """创建目录结构"""
    print(f"[init] 创建根目录: {PROPOSALS_ROOT}")
    PROPOSALS_ROOT.mkdir(parents=True, exist_ok=True)

    for subdir in SUBDIRS:
        path = PROPOSALS_ROOT / subdir
        if path.is_dir():
            print(f"[init] 跳过（已存在）: {subdir}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"[init] 创建: {subdir}/")

    for csv_file, header in CSV_FILES.items():
        path = PROPOSALS_ROOT / csv_file
        if path.exists() and path.stat().st_size > 0:
            print(f"[init] 跳过（已存在且非空）: {csv_file}")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header)
            print(f"[init] 创建: {csv_file}")

    for md_file, content in MD_FILES.items():
        path = PROPOSALS_ROOT / md_file
        if path.exists() and path.stat().st_size > 0:
            print(f"[init] 跳过（已存在且非空）: {md_file}")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[init] 创建: {md_file}")


def main():
    print(f"[init] 检查目录: {PROPOSALS_ROOT}")

    if not PROPOSALS_ROOT.exists():
        print("[init] 根目录不存在，开始初始化...")
        init_dirs()
        print("[init] 初始化完成")
        return

    missing = check_initialized()
    if not missing:
        print("[init] 已初始化，跳过")
        return

    print("[init] 检测到未初始化的内容:")
    for m in missing:
        print(m)

    # 检查是否有 CSV 内容（已有数据则不能初始化）
    csv_with_data = []
    for csv_file in ["projects.csv", "proposals.csv"]:
        path = PROPOSALS_ROOT / csv_file
        if path.exists() and path.stat().st_size > 0:
            # 检查是否有数据行（不只是表头）
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > 1:
                csv_with_data.append(csv_file)

    if csv_with_data:
        print(f"\n[init] 以下 CSV 已存在数据，强制初始化会丢失，退出:")
        for f in csv_with_data:
            print(f"  - {f}")
        sys.exit(1)

    init_dirs()
    print("[init] 初始化完成")


if __name__ == "__main__":
    main()
