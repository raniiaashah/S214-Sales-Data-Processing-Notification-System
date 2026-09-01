# S214 Sales Platform - Troubleshooting Guide

## Common Issues

### Stack Creation Fails

#### Symptom
CloudFormation stack creation fails with an error.

#### Possible Causes
- Insufficient IAM permissions
- Invalid template syntax
- Resource limits exceeded
- VPC CIDR conflicts

#### Solutions
1. Check CloudFormation events in AWS Console:
   ```bash
   aws cloudformation describe-stack-events --stack-name s214-dev-sales-platform
   ```

2. Validate templates locally:
   ```bash
   cfn-lint infrastructure/*.yaml
   ```

3. Verify IAM permissions for the deploying user/role

4. Check AWS service limits

### Lambda Timeout

#### Symptom
Lambda function times out during execution.

#### Possible Causes
- Database connection issues
- Insufficient Lambda timeout configuration
- VPC configuration problems
- Security group misconfiguration

#### Solutions
1. Check Lambda logs in CloudWatch:
   ```bash
   aws logs tail /aws/lambda/s214-dev-sales-processor --follow
   ```

2. Increase Lambda timeout in configuration

3. Verify security group rules allow Lambda to RDS communication

4. Ensure Lambda is in correct subnets

### Database Connection Failed

#### Symptom
Lambda cannot connect to RDS.

#### Possible Causes
- Incorrect credentials in Secrets Manager
- Security group not allowing traffic
- RDS not yet available
- Wrong endpoint configured

#### Solutions
1. Verify Secrets Manager credentials:
   ```bash
   aws secretsmanager get-secret-value --secret-id s214-dev/database/credentials
   ```

2. Check RDS security group rules

3. Verify RDS instance is in "available" state:
   ```bash
   aws rds describe-db-instances --db-instance-identifier s214-dev-rds
   ```

4. Ensure Lambda is in private subnets

### SNS Email Not Received

#### Symptom
Sales reports are not received via email.

#### Possible Causes
- Email subscription not confirmed
- Email in spam/junk folder
- SNS topic not configured correctly
- Lambda not publishing to SNS

#### Solutions
1. Check subscription status in SNS console

2. Look for confirmation email and click the link

3. Check spam/junk folder

4. Verify Lambda is publishing to SNS:
   ```bash
   aws logs tail /aws/lambda/s214-dev-sales-processor --follow
   ```

### High Lambda Costs

#### Symptom
Unexpectedly high Lambda costs.

#### Possible Causes
- High invocation count
- Long execution time
- High memory allocation

#### Solutions
1. Check Lambda metrics in CloudWatch

2. Optimize Lambda code for performance

3. Right-size memory allocation

4. Check for infinite loops or retries

### RDS High Storage

#### Symptom
RDS storage is running low.

#### Possible Causes
- Large amount of sales data
- Autoscaling not enabled
- Backup retention too high

#### Solutions
1. Check RDS storage metrics in CloudWatch

2. Enable storage autoscaling (already configured)

3. Adjust backup retention period

4. Archive old data if needed

## Debug Mode

### Enable Debug Logging
Set the `LOG_LEVEL` environment variable to `DEBUG` in Lambda configuration.

### View Logs
```bash
# Processor Lambda logs
aws logs tail /aws/lambda/s214-dev-sales-processor --follow

# Custom Resource Lambda logs
aws logs tail /aws/lambda/s214-dev-custom-resource --follow
```

### Test Lambda Locally
```bash
cd src/processor
python3 -c "
import os
os.environ['SECRET_ARN'] = 'your-secret-arn'
os.environ['SNS_TOPIC_ARN'] = 'your-topic-arn'
os.environ['ENVIRONMENT'] = 'dev'
from lambda_function import lambda_handler
result = lambda_handler({}, {})
print(result)
"
```

## CloudWatch Metrics

### Key Metrics to Monitor

| Metric | Namespace | Description |
|--------|-----------|-------------|
| Invocations | AWS/Lambda | Number of Lambda invocations |
| Errors | AWS/Lambda | Number of failed invocations |
| Duration | AWS/Lambda | Execution time in milliseconds |
| Throttles | AWS/Lambda | Number of throttled invocations |
| CPUUtilization | AWS/RDS | RDS CPU usage |
| FreeStorageSpace | AWS/RDS | RDS free storage |

### Create Custom Metrics
```bash
aws cloudwatch put-metric-data \
  --namespace "S214/Custom" \
  --metric-name "SalesProcessed" \
  --value 100 \
  --unit Count
```

## Getting Help

### AWS Documentation
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [RDS User Guide](https://docs.aws.amazon.com/rds/)

### GitHub Issues
If you encounter a bug, please open an issue on GitHub with:
- Description of the problem
- Steps to reproduce
- Error messages
- AWS region

### AWS Support
For AWS-specific issues, consider:
- AWS Support Center
- AWS Developer Forums
- Stack Overflow (tag with aws-cloudformation)