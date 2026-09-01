#!/bin/bash
# ============================================
# S214 Sales Platform - Deploy Script
# ============================================
# This script deploys the CloudFormation stack
# to the specified environment.
#
# Usage: ./scripts/deploy.sh <environment>
# Example: ./scripts/deploy.sh dev
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

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  S214 Sales Platform - Deploy${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Stack Name:  ${STACK_NAME}"
echo "Region:      ${REGION}"
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

# Get notification email
NOTIFICATION_EMAIL=${NOTIFICATION_EMAIL:-"user@example.com"}
echo "Notification Email: ${NOTIFICATION_EMAIL}"
echo ""

# Create artifacts bucket
BUCKET_NAME="s214-${ENVIRONMENT}-artifacts-$(date +%s)"
echo -e "${YELLOW}Creating artifacts bucket: ${BUCKET_NAME}${NC}"
aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}" || true

# Package Lambda functions
echo -e "${YELLOW}Packaging Lambda functions...${NC}"
mkdir -p packages

# Package processor Lambda
cd src/processor
pip install -r requirements.txt -t . --quiet
zip -r ../../packages/processor.zip . -x "*.pyc" "__pycache__/*" > /dev/null
cd ../..

# Package custom resource Lambda
cd src/custom-resource
pip install -r requirements.txt -t . --quiet
zip -r ../../packages/custom-resource.zip . -x "*.pyc" "__pycache__/*" > /dev/null
cd ../..

echo -e "${GREEN}✓ Lambda packages created${NC}"

# Upload to S3
echo -e "${YELLOW}Uploading to S3...${NC}"
aws s3 cp packages/processor.zip "s3://${BUCKET_NAME}/lambda/processor.zip"
aws s3 cp packages/custom-resource.zip "s3://${BUCKET_NAME}/lambda/custom-resource.zip"
aws s3 cp infrastructure/ "s3://${BUCKET_NAME}/templates/" --recursive

echo -e "${GREEN}✓ Files uploaded to S3${NC}"
echo ""

# Deploy CloudFormation stack
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"
echo ""

aws cloudformation deploy \
    --template-file infrastructure/root.yaml \
    --stack-name "${STACK_NAME}" \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
        LambdaCodeBucket="${BUCKET_NAME}" \
        NotificationEmail="${NOTIFICATION_EMAIL}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

echo ""
echo -e "${GREEN}✓ Stack deployment initiated${NC}"
echo ""

# Wait for stack completion
echo -e "${YELLOW}Waiting for stack to complete...${NC}"

if aws cloudformation wait stack-create-complete --stack-name "${STACK_NAME}" 2>/dev/null || \
   aws cloudformation wait stack-update-complete --stack-name "${STACK_NAME}" 2>/dev/null; then
    echo -e "${GREEN}✓ Stack deployment completed${NC}"
else
    echo -e "${RED}✗ Stack deployment failed${NC}"
    echo "Check CloudFormation console for details"
    exit 1
fi

echo ""

# Display stack outputs
echo -e "${YELLOW}Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Stack Name: ${STACK_NAME}"
echo "Region:     ${REGION}"
echo ""
echo "Note: SNS email subscription requires confirmation."
echo "      Check your email for a confirmation link."