#!/usr/bin/env bash
# check-persona-docs.sh — Verify USER.md, SOUL.md, MEMORY.md compliance
# Part of prj-proposals-manager skill (v3.3.0+)
# Usage: bash scripts/check-persona-docs.sh [--verbose]

set -euo pipefail
TEMPLATES_DIR="${TEMPLATES_DIR:-/home/hermes/proposals/templates}"
VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

errors=0
warnings=0

check_file() {
    local file="$1"
    local desc="$2"
    local min_lines="${3:-10}"
    
    if [ -f "$TEMPLATES_DIR/$file" ]; then
        local lines
        lines=$(wc -l < "$TEMPLATES_DIR/$file")
        if [ "$lines" -ge "$min_lines" ]; then
            $VERBOSE && echo "  ✅ $file ($lines lines)"
        else
            echo "  ⚠️  $file too short ($lines lines, expected >= $min_lines)"
            warnings=$((warnings + 1))
        fi
    else
        echo "  ❌ $file MISSING"
        errors=$((errors + 1))
    fi
}

check_section() {
    local file="$1"
    local keyword="$2"
    local desc="$3"
    
    if [ -f "$TEMPLATES_DIR/$file" ]; then
        if grep -q "$keyword" "$TEMPLATES_DIR/$file" 2>/dev/null; then
            $VERBOSE && echo "    ✓ $desc"
        else
            echo "    ⚠️  $desc — section '$keyword' not found in $file"
            warnings=$((warnings + 1))
        fi
    fi
}

echo "=== Persona Docs Compliance Check ==="
echo "Templates: $TEMPLATES_DIR"
echo ""

# Core file existence
echo "Core files:"
check_file "USER.md" "User profile" 20
check_file "SOUL.md" "Agent soul" 30
check_file "MEMORY.md" "Memory management" 40
echo ""

# USER.md content checks
echo "USER.md sections:"
check_section "USER.md" "基本信息" "Basic info"
check_section "USER.md" "工作流偏好" "Workflow preferences"
check_section "USER.md" "GitHub 偏好" "GitHub preferences"
check_section "USER.md" "项目偏好" "Project preferences"
check_section "USER.md" "更新日志" "Changelog"
echo ""

# SOUL.md content checks
echo "SOUL.md sections:"
check_section "SOUL.md" "身份" "Identity"
check_section "SOUL.md" "灵魂特质" "Soul traits"
check_section "SOUL.md" "核心准则" "Core principles"
check_section "SOUL.md" "能力矩阵" "Capability matrix"
check_section "SOUL.md" "迭代偏好" "Iteration preferences"
echo ""

# MEMORY.md content checks
echo "MEMORY.md sections:"
check_section "MEMORY.md" "记忆分层架构" "Memory hierarchy"
check_section "MEMORY.md" "存储策略" "Storage strategy"
check_section "MEMORY.md" "更新触发条件" "Update triggers"
check_section "MEMORY.md" "重要经验沉淀" "Experience repository"
echo ""

# Memory directory
if [ -d "/home/hermes/proposals/memory/" ]; then
    local daily_count
    daily_count=$(find /home/hermes/proposals/memory/ -name "????-??-??.md" 2>/dev/null | wc -l)
    $VERBOSE && echo "✅ memory/ exists ($daily_count daily logs)"
else
    echo "⚠️  memory/ directory missing"
    warnings=$((warnings + 1))
fi

# Audit log
if [ -f "/home/hermes/proposals/audit.log" ]; then
    local audit_lines
    audit_lines=$(wc -l < /home/hermes/proposals/audit.log)
    $VERBOSE && echo "✅ audit.log exists ($audit_lines entries)"
else
    $VERBOSE && echo "ℹ️  audit.log not yet created (will be created on first CSV write)"
fi

echo ""
echo "---"
echo "Results: $errors errors, $warnings warnings"
if [ "$errors" -gt 0 ]; then
    echo "❌ FAIL — $errors error(s) found"
    exit 1
elif [ "$warnings" -gt 0 ]; then
    echo "⚠️  PASS with warnings"
    exit 0
else
    echo "✅ PASS"
    exit 0
fi
