# S214 Sales Platform - Architecture Documentation

## Overview

This document explains the architecture of the S214 Sales Platform, including design decisions, security considerations, and data flow.

## Architecture Diagram

```
                GitHub
                   |
                   v
              CI/CD Pipeline
                   |
                   v
            CloudFormation
                   |
                   v
                 AWS
                   |
    +--------------+--------------+
    |                             |
    v                             v
   VPC                     Secrets Manager
    |
    +----+-----------------------+
         |                       |
         v                       v
    Private Subnets            Public Subnets
         |
         +----------+
         |          |
         v          v
        RDS       Lambda
         |
         +------+------+
         |             |
         v             v
        SNS        CloudWatch
         |
         v
        Email

    EventBridge
         |
         v
       Lambda
```

## Why VPC is Used

The VPC provides network isolation and security for all resources:

- **Network Segmentation**: Public and private subnets separate internet-facing resources from internal resources
- **Security**: Network ACLs and security groups control traffic flow
- **Compliance**: Many compliance frameworks require network isolation

## Why RDS is Private

RDS is deployed in private subnets for security:

- **No Public Access**: Database is not accessible from the internet
- **Reduced Attack Surface**: Only Lambda functions in the VPC can access the database
- **Compliance**: Meets security best practices for database deployment

## Why Lambda is Inside the VPC

Lambda functions run in the VPC to access RDS:

- **Database Access**: Lambda needs to be in the VPC to connect to private RDS
- **Security Groups**: Lambda uses security groups to control outbound traffic
- **NAT Gateway**: Lambda uses NAT Gateway for outbound internet access (AWS API calls)

## Why Secrets Manager is Used

Secrets Manager securely stores database credentials:

- **Encryption**: Secrets are encrypted at rest and in transit
- **Rotation**: Supports automatic credential rotation
- **Access Control**: IAM policies control who can access secrets
- **Audit Trail**: CloudTrail logs all access to secrets

## Why SSM Parameter Store is Used

SSM Parameter Store stores non-sensitive configuration:

- **Resource References**: Stores VPC IDs, ARNs, endpoints
- **Hierarchical Organization**: Parameters organized by environment
- **Version Tracking**: Tracks changes to parameter values
- **Free to Use**: No additional cost for standard parameters

## Why EventBridge is Used

EventBridge provides scheduled execution:

- **Serverless**: No infrastructure to manage
- **Flexible Scheduling**: Supports cron and rate expressions
- **Reliable**: Managed service with high availability
- **Integration**: Native integration with Lambda

## Why SNS is Used

SNS delivers notifications:

- **Multiple Protocols**: Supports email, SMS, Lambda, etc.
- **Fan-out**: One message can reach multiple subscribers
- **Reliable**: Managed service with retry logic
- **Encryption**: Supports encryption in transit and at rest

## Why CloudFormation is Used

CloudFormation provides Infrastructure as Code:

- **Reproducibility**: Infrastructure can be recreated consistently
- **Version Control**: Templates can be stored in Git
- **Rollback**: Automatic rollback on deployment failure
- **Dependency Management**: Handles resource dependencies automatically

## Why GitHub Actions is Used

GitHub Actions provides CI/CD automation:

- **Integrated**: Native integration with GitHub
- **OIDC Support**: Secure authentication with AWS without storing credentials
- **Matrix Builds**: Test multiple configurations in parallel
- **Marketplace**: Large ecosystem of actions

## Security Boundaries

### Network Boundaries
- **Internet Gateway**: Controls inbound/outbound internet traffic
- **NAT Gateway**: Allows private subnets to access the internet
- **Security Groups**: Stateful firewall for resources
- **NACLs**: Stateless firewall for subnets

### IAM Boundaries
- **Least Privilege**: Each role has minimum required permissions
- **No Wildcards**: No use of `*` in IAM policies
- **Service Roles**: Dedicated roles for each service

### Data Boundaries
- **Encryption at Rest**: RDS, Secrets Manager, SNS
- **Encryption in Transit**: TLS for all connections
- **No Hardcoded Secrets**: All secrets stored in Secrets Manager

## Data Flow

### Sales Processing Flow
1. EventBridge triggers Lambda on schedule
2. Lambda retrieves credentials from Secrets Manager
3. Lambda connects to RDS in private subnet
4. Lambda queries sales data
5. Lambda calculates metrics
6. Lambda generates report
7. Lambda publishes report to SNS
8. SNS sends email to subscribers

### Deployment Flow
1. Developer pushes code to GitHub
2. GitHub Actions runs CI pipeline
3. Tests and security scans execute
4. Lambda packages are created
5. Packages uploaded to S3
6. CloudFormation deploys stack
7. Custom Resource initializes database
8. Stack outputs are displayed

## Cost Optimization

### Development Environment
- **NAT Gateway**: ~$33/month (use VPC endpoints to reduce)
- **RDS db.t3.micro**: ~$13/month
- **Lambda**: Free tier eligible
- **Total**: ~$47/month

### Production Optimization
- **Reserved Instances**: For RDS to reduce costs
- **VPC Endpoints**: Reduce NAT Gateway data processing
- **Lambda Optimization**: Right-size memory and timeout
- **CloudWatch**: Set log retention policies

## Disaster Recovery

### Backup Strategy
- **RDS**: Automated daily backups with configurable retention
- **Infrastructure**: CloudFormation templates in version control
- **Secrets**: Secrets Manager with automatic rotation

### Recovery Procedures
1. **Infrastructure Loss**: Redeploy from CloudFormation templates
2. **Database Failure**: Restore from automated backups
3. **Secrets Loss**: Recreate secrets and update references