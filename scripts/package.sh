#!/bin/bash
# ============================================
# S214 Sales Platform - Package Script
# ============================================
# This script packages Lambda functions for deployment.
#
# Usage: ./scripts/package.sh
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  S214 Sales Platform - Packaging${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check if required tools are installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed${NC}"
    exit 1
fi

# Create packages directory
mkdir -p packages

# Package processor Lambda
echo -e "${YELLOW}Packaging processor Lambda...${NC}"
cd src/processor
pip install -r requirements.txt -t . --quiet
zip -r ../../packages/processor.zip . -x "*.pyc" "__pycache__/*" "*.egg-info/*" > /dev/null
cd ../..
echo -e "${GREEN}✓ Processor Lambda packaged${NC}"

# Package custom resource Lambda
echo -e "${YELLOW}Packaging custom resource Lambda...${NC}"
cd src/custom-resource
pip install -r requirements.txt -t . --quiet
zip -r ../../packages/custom-resource.zip . -x "*.pyc" "__pycache__/*" "*.egg-info/*" > /dev/null
cd ../..
echo -e "${GREEN}✓ Custom resource Lambda packaged${NC}"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Packaging Complete${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Packages created:"
ls -lh packages/