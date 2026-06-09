#!/bin/bash
#================================================================
# 提案系统备份脚本
# 备份内容：project-index.md、proposal-docs-index.md、
#           proposal-index.md、templates、projects.csv、proposals.csv
#================================================================

set -e

SKILL_NAME="prj-proposals-manager"
SKILL_DIR="/home/hermes/.hermes/skills/${SKILL_NAME}"
BACKUP_ROOT="/home/hermes/proposals/backups"
PROPOSALS_ROOT="/home/hermes/proposals"

# 创建备份目录（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/backup_${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"

echo "📦 提案系统备份"
echo "=================="
echo "备份目录: ${BACKUP_DIR}"
echo ""

# 备份文件列表
BACKUP_FILES=(
    "${PROPOSALS_ROOT}/project-index.md"
    "${PROPOSALS_ROOT}/proposal-docs-index.md"
    "${PROPOSALS_ROOT}/proposal-index.md"
    "${PROPOSALS_ROOT}/projects.csv"
    "${PROPOSALS_ROOT}/proposals.csv"
)

# 备份模板目录
TEMPLATES_DIR="${PROPOSALS_ROOT}/templates"

# 统计
total=0
success=0
failed=0

# 备份单个文件
backup_file() {
    local src="$1"
    local dest="$2"
    local name=$(basename "$src")
    
    if [ -f "$src" ]; then
        cp "$src" "$dest"
        echo "  ✅ $name"
        success=$((success + 1))
    elif [ -d "$src" ]; then
        cp -r "$src" "$dest"
        echo "  ✅ $name/ (目录)"
        success=$((success + 1))
    else
        echo "  ⚠️  不存在: $name"
        failed=$((failed + 1))
    fi
    total=$((total + 1))
}

# 备份提案数据和技能
echo "📄 备份提案数据..."
for file in "${BACKUP_FILES[@]}"; do
    backup_file "$file" "${BACKUP_DIR}/"
done

# 备份模板目录
backup_file "$TEMPLATES_DIR" "${BACKUP_DIR}/"

# 备份技能文件
echo ""
echo "📦 备份技能文件..."
SKILL_FILES=(
    "${SKILL_DIR}/SKILL.md"
    "${SKILL_DIR}/SKILL-zh.md"
    "${SKILL_DIR}/scripts/proposal_manager_cli.py"
    "${SKILL_DIR}/scripts/sync-proposals-to-website.py"
    "${SKILL_DIR}/scripts/rollback_proposals.sh"
    "${SKILL_DIR}/scripts/backup_proposals.sh"
    "${SKILL_DIR}/scripts/edit_proposal.py"
    "${SKILL_DIR}/scripts/init_proposals_dir.py"
)

SKILL_SUBDIRS=("references")
for subdir in "${SKILL_SUBDIRS[@]}"; do
    if [ -d "${SKILL_DIR}/${subdir}" ]; then
        backup_file "${SKILL_DIR}/${subdir}" "${BACKUP_DIR}/skill_${subdir}/"
    fi
done

for file in "${SKILL_FILES[@]}"; do
    backup_file "$file" "${BACKUP_DIR}/"
done

echo ""

# 生成备份清单
{
    echo "# 备份清单 - ${TIMESTAMP}"
    echo ""
    echo "## 备份内容"
    echo ""
    echo "| 类型 | 名称 | 状态 |"
    echo "|------|------|------|"
    for item in $(ls -A "${BACKUP_DIR}" 2>/dev/null); do
        if [ -d "${BACKUP_DIR}/$item" ]; then
            count=$(find "${BACKUP_DIR}/$item" -name "*.md" -o -name "*.csv" 2>/dev/null | wc -l)
            echo "| 目录 | $item | ✅ ($count 文件) |"
        else
            echo "| 文件 | $item | ✅ |"
        fi
    done
    echo ""
    echo "## 备份信息"
    echo ""
    echo "- 备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "- 备份路径: ${BACKUP_DIR}"
    echo "- 成功: ${success}/${total}"
    if [ $failed -gt 0 ]; then
        echo "- 失败/跳过: ${failed}"
    fi
} > "${BACKUP_DIR}/MANIFEST.md"

# 更新最新备份软链接
rm -f "${BACKUP_ROOT}/latest"
ln -s "${BACKUP_DIR}" "${BACKUP_ROOT}/latest"

echo "📋 备份清单已生成: ${BACKUP_DIR}/MANIFEST.md"
echo ""
echo "✅ 备份完成！"
echo "   最新备份: ${BACKUP_ROOT}/latest"
echo "   本次备份: ${BACKUP_DIR}"

# 保留最近 10 个备份，清理旧备份
echo ""
echo "🧹 清理旧备份（保留最近 10 个）..."
backup_count=$(ls -d "${BACKUP_ROOT}"/backup_* 2>/dev/null | wc -l)
if [ $backup_count -gt 10 ]; then
    old_backups=$(ls -d "${BACKUP_ROOT}"/backup_* 2>/dev/null | sort | head -n -10)
    for old_dir in $old_backups; do
        rm -rf "$old_dir"
        echo "  🗑️  已删除: $(basename $old_dir)"
    done
    echo "   已清理 $((backup_count - 10)) 个旧备份"
else
    echo "   无需清理，当前共 ${backup_count} 个备份"
fi
