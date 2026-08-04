#!/bin/bash
# CI 本地检查脚本
# 用法: ./scripts/ci.sh [--fix] [--skip-tests]

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 参数解析
FIX=false
SKIP_TESTS=false
for arg in "$@"; do
    case $arg in
        --fix)
            FIX=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
    esac
done

echo "=========================================="
echo "🔍 WeatherAgent CI 检查"
echo "=========================================="
echo ""

# ============ 代码检查 ============
echo -e "${YELLOW}📝 代码检查 (Ruff Lint)${NC}"
if [ "$FIX" = true ]; then
    echo "  自动修复模式..."
    ruff check . --fix
else
    ruff check .
fi
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✅ 代码检查通过${NC}"
else
    echo -e "  ${RED}❌ 代码检查失败${NC}"
    exit 1
fi
echo ""

# ============ 代码格式检查 ============
echo -e "${YELLOW}🎨 代码格式检查 (Ruff Format)${NC}"
if [ "$FIX" = true ]; then
    echo "  自动格式化..."
    ruff format .
else
    ruff format --check .
fi
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✅ 代码格式正确${NC}"
else
    echo -e "  ${RED}❌ 代码格式不正确${NC}"
    echo "  运行 ./scripts/ci.sh --fix 自动修复"
    exit 1
fi
echo ""

# ============ 类型检查 ============
echo -e "${YELLOW}📊 类型检查 (Mypy)${NC}"
mypy app/ --ignore-missing-imports --no-error-summary 2>/dev/null || true
echo -e "  ${GREEN}✅ 类型检查完成（警告不阻断）${NC}"
echo ""

# ============ 运行测试 ============
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${YELLOW}🧪 运行测试 (Pytest)${NC}"
    pytest tests/ -v --tb=short -q
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ 测试通过${NC}"
    else
        echo -e "  ${RED}❌ 测试失败${NC}"
        exit 1
    fi
    echo ""

    # ============ 测试覆盖率 ============
    echo -e "${YELLOW}📈 测试覆盖率${NC}"
    pytest tests/ --cov=app --cov-report=term-missing --cov-report=html -q
    echo ""
fi

echo "=========================================="
echo -e "${GREEN}✅ CI 检查全部通过！${NC}"
echo "=========================================="
