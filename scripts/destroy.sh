#!/bin/bash
# ============================================
# S214 Sales Platform - Destroy Script
# ============================================
# This script destroys the CloudFormation stack
# for the specified environment.
#
# WARNING: This will delete all resources including data!
#
# Usage: ./scripts/destroy.sh <environment>
# Example: ./scripts/destroy.sh dev
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Environment not specified${NC}"
    echo "Usage: $0 <environment>"
    echo "Environments: dev, staging, prod"
    exit 1
fi

ENVIRONMENT=$1
STACK_NAME="s214-${ENVIRONMENT}-sales-platform"
REGION="us-east-1"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Valid environments: dev, staging, prod"
    exit 1
fi

echo -e "${RED}============================================${NC}"
echo -e "${RED}  S214 Sales Platform - Destroy${NC}"
echo -e "${RED}============================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Stack Name:  ${STACK_NAME}"
echo "Region:      ${REGION}"
echo ""
echo -e "${RED}WARNING: This will delete all resources including data!${NC}"
echo ""

# Confirm deletion
read -p "Are you sure you want to delete this stack? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deletion cancelled"
    exit 0
fi

echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run 'aws configure' or set environment variables"
    exit 1
fi

# Delete CloudFormation stack
echo -e "${YELLOW}Deleting CloudFormation stack...${NC}"

aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}"

echo -e "${GREEN}✓ Stack deletion initiated${NC}"
echo ""

# Wait for stack deletion
echo -e "${YELLOW}Waiting for stack deletion to complete...${NC}"

if aws cloudformation wait stack-delete-complete \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" 2>/dev/null; then
    echo -e "${GREEN}✓ Stack deletion completed${NC}"
else
    echo -e "${RED}✗ Stack deletion failed${NC}"
    echo "Check CloudFormation console for details"
    exit 1
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Stack Deleted Successfully${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Stack Name: ${STACK_NAME}"
echo "Region:     ${REGION}"
echo ""
echo "Note: S3 buckets and snapshots may still exist."
echo "      Clean up manually if needed."