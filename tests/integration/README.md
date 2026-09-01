# Integration Tests

## Overview

Integration tests require a real AWS account and deployed infrastructure. These tests verify that all components work together correctly.

## Prerequisites

- AWS account with deployed S214 stack
- AWS CLI configured with appropriate permissions
- Python 3.11+

## Setup

1. Install dependencies:
```bash
pip install -r src/processor/requirements.txt
pip install pytest boto3
```

2. Set environment variables:
```bash
export SECRET_ARN=arn:aws:secretsmanager:region:account:secret:name
export SNS_TOPIC_ARN=arn:aws:sns:region:account:topic-name
export ENVIRONMENT=dev
export AWS_REGION=us-east-1
```

## Running Tests

```bash
pytest tests/integration/ -v
```

## Test Cases

### Database Connection Test
- Verifies Lambda can connect to RDS
- Tests credential retrieval from Secrets Manager

### Sales Processing Test
- Inserts test data into database
- Triggers Lambda function
- Verifies report generation

### SNS Notification Test
- Verifies Lambda can publish to SNS
- Checks message delivery

### End-to-End Test
- Full workflow test from trigger to notification

## Cleanup

Integration tests may create test data. Run cleanup after tests:

```python
# Clean up test data
import boto3
# ... cleanup code
```

## CI/CD Integration

Integration tests are not run in the CI pipeline by default. They should be run manually or in a separate workflow with appropriate AWS credentials.

## Security Note

Integration tests require AWS credentials with permissions to:
- Read from Secrets Manager
- Write to RDS
- Publish to SNS
- Invoke Lambda functions

Use a dedicated test environment and never run integration tests against production.