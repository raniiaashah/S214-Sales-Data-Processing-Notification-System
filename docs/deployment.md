# S214 Sales Platform - Deployment Guide

## Prerequisites

### Required Tools
- AWS CLI v2.0+
- Python 3.11+
- Git

### AWS Requirements
- AWS Account with appropriate limits
- IAM user/role with CloudFormation deployment permissions
- Configured AWS CLI credentials

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/username/s214-sales-platform.git
cd s214-sales-platform
```

### 2. Configure AWS Credentials
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### 3. Set Notification Email
```bash
export NOTIFICATION_EMAIL=your-email@example.com
```

### 4. Validate Templates
```bash
./scripts/validate.sh
```

### 5. Run Tests
```bash
./scripts/test.sh
```

### 6. Deploy
```bash
./scripts/deploy.sh dev
```

## Deployment Scripts

### validate.sh
Validates all CloudFormation templates and runs linting checks:
```bash
./scripts/validate.sh
```

### test.sh
Runs all unit tests and generates coverage report:
```bash
./scripts/test.sh
```

### package.sh
Packages Lambda functions for deployment:
```bash
./scripts/package.sh
```

### deploy.sh
Deploys the CloudFormation stack:
```bash
./scripts/deploy.sh <environment>
# Example: ./scripts/deploy.sh dev
```

### destroy.sh
Destroys the CloudFormation stack:
```bash
./scripts/destroy.sh <environment>
# Example: ./scripts/destroy.sh dev
```

## Manual Deployment

### Step 1: Package Lambda Functions
```bash
mkdir -p packages

# Package processor Lambda
cd src/processor
pip install -r requirements.txt -t .
zip -r ../../packages/processor.zip .
cd ../..

# Package custom resource Lambda
cd src/custom-resource
pip install -r requirements.txt -t .
zip -r ../../packages/custom-resource.zip .
cd ../..
```

### Step 2: Create S3 Bucket
```bash
aws s3 mb s3://s214-artifacts-bucket --region us-east-1
```

### Step 3: Upload to S3
```bash
# Upload Lambda packages
aws s3 cp packages/processor.zip s3://s214-artifacts-bucket/lambda/processor.zip
aws s3 cp packages/custom-resource.zip s3://s214-artifacts-bucket/lambda/custom-resource.zip

# Upload CloudFormation templates
aws s3 cp infrastructure/ s3://s214-artifacts-bucket/templates/ --recursive
```

### Step 4: Deploy CloudFormation Stack
```bash
aws cloudformation deploy \
  --template-file infrastructure/root.yaml \
  --stack-name s214-dev-sales-platform \
  --parameter-overrides \
    Environment=dev \
    LambdaCodeBucket=s214-artifacts-bucket \
    NotificationEmail=your-email@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset
```

### Step 5: Wait for Deployment
```bash
aws cloudformation wait stack-create-complete \
  --stack-name s214-dev-sales-platform
```

### Step 6: Get Stack Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name s214-dev-sales-platform \
  --query 'Stacks[0].Outputs' \
  --output table
```

## CI/CD Deployment

### GitHub Actions OIDC Setup

1. Create an IAM OIDC Provider:
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --thumbprint-list <thumbprint> \
  --client-id-list sts.amazonaws.com
```

2. Create an IAM Role with trust policy for GitHub

3. Add the role ARN as a GitHub Secret (`AWS_ROLE_ARN`)

4. Push to main branch to trigger deployment

## Post-Deployment

### Confirm SNS Subscription
1. Check your email for a subscription confirmation
2. Click the confirmation link
3. Future reports will be delivered to your email

### Verify Deployment
1. Check CloudFormation stack status
2. Verify Lambda functions are created
3. Check RDS instance is running
4. Test EventBridge rule

## Troubleshooting

### Stack Creation Fails
- Check CloudFormation events in AWS Console
- Verify IAM permissions
- Validate template syntax with `cfn-lint`

### Lambda Timeout
- Increase Lambda timeout in configuration
- Check RDS security group rules
- Verify VPC configuration

### Database Connection Failed
- Verify Secrets Manager credentials
- Check security group rules
- Ensure Lambda is in correct subnets

### SNS Email Not Received
- Confirm email subscription
- Check spam/junk folder
- Verify SNS topic configuration

## Cleanup

### Destroy Stack
```bash
./scripts/destroy.sh dev
```

### Manual Cleanup
```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name s214-dev-sales-platform

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name s214-dev-sales-platform

# Delete S3 bucket
aws s3 rb s3://s214-artifacts-bucket --force