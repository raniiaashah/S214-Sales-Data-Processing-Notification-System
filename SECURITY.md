# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before disclosure

## Security Measures

### Network Security
- VPC with public/private subnet isolation
- RDS in private subnets (no public access)
- Security groups with least-privilege access
- NAT Gateway for controlled outbound access

### Data Security
- AWS Secrets Manager for credential storage
- RDS encryption at rest
- SNS topic encryption
- No hardcoded secrets in code

### Access Control
- IAM least-privilege policies
- Dedicated IAM roles per Lambda function
- No wildcard permissions
- OIDC for CI/CD authentication

### Security Scanning
- Bandit for Python code analysis
- pip-audit for dependency vulnerabilities
- cfn-lint for CloudFormation security
- Trivy for comprehensive vulnerability scanning

## Dependencies

We regularly scan dependencies for known vulnerabilities. Keep dependencies updated to the latest secure versions.

## AWS Best Practices

This project follows AWS Well-Architected Framework security best practices:
- Implement least privilege access
- Enable encryption at rest and in transit
- Monitor and log all actions
- Automate security testing