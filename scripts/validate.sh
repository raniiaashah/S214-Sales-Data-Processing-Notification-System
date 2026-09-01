#!/bin/bash
# ============================================
# S214 Sales Platform - Validation Script
# ============================================
# This script validates all CloudFormation templates
# and runs linting checks before deployment.
#
# Usage: ./scripts/validate.sh
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  S214 Sales Platform - Validation${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ $1 is installed${NC}"
}

echo "Checking required tools..."
check_tool python3
check_tool pip
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install flake8 cfn-lint bandit --quiet
echo ""

# Validate CloudFormation templates
echo -e "${YELLOW}Validating CloudFormation templates...${NC}"
echo ""

TEMPLATES=(
    "infrastructure/vpc.yaml"
    "infrastructure/security-groups.yaml"
    "infrastructure/iam.yaml"
    "infrastructure/secrets.yaml"
    "infrastructure/rds.yaml"
    "infrastructure/sns.yaml"
    "infrastructure/lambda.yaml"
    "infrastructure/eventbridge.yaml"
    "infrastructure/root.yaml"
)

VALIDATION_PASSED=true

for template in "${TEMPLATES[@]}"; do
    echo -n "  Validating $template... "
    if cfn-lint "$template" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        VALIDATION_PASSED=false
    fi
done

echo ""

# Run Python linting
echo -e "${YELLOW}Running Python linting...${NC}"
echo ""

echo -n "  Linting src/... "
if flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null; then
    echo -e "${GREEN}PASSED${NC}"
else
    echo -e "${YELLOW}WARNINGS${NC}"
fi

echo -n "  Linting tests/... "
if flake8 tests/ --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null; then
    echo -e "${GREEN}PASSED${NC}"
else
    echo -e "${YELLOW}WARNINGS${NC}"
fi

echo ""

# Run security scan
echo -e "${YELLOW}Running security scan...${NC}"
echo ""

echo -n "  Scanning src/ with Bandit... "
if bandit -r src/ -ll --quiet 2>/dev/null; then
    echo -e "${GREEN}PASSED${NC}"
else
    echo -e "${YELLOW}WARNINGS${NC}"
fi

echo ""

# Summary
echo -e "${GREEN}============================================${NC}"
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}  Validation Completed Successfully${NC}"
else
    echo -e "${RED}  Validation Completed with Errors${NC}"
    exit 1
fi
echo -e "${GREEN}============================================${NC}"