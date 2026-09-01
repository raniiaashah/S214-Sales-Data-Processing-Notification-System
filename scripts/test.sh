#!/bin/bash
# ============================================
# S214 Sales Platform - Test Script
# ============================================
# This script runs all unit tests and generates
# a coverage report.
#
# Usage: ./scripts/test.sh
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  S214 Sales Platform - Running Tests${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check if required tools are installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-cov --quiet
pip install -r src/processor/requirements.txt --quiet
echo ""

# Run unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
echo ""

cd "$(dirname "$0")/.."

if python3 -m pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-report=html; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  All Tests Passed${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Coverage report generated: htmlcov/index.html"
else
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}  Tests Failed${NC}"
    echo -e "${RED}============================================${NC}"
    exit 1
fi