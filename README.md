# KustForge - AWS Resource Template Processor

KustForge is a Python-based tool for processing Kubernetes manifests and other templates with dynamic AWS resource resolution. This tool helps bridge the gap between infrastructure-as-code and AWS resources by allowing dynamic resolution of AWS resource attributes in your templates.

## Features

- Dynamic AWS resource resolution in templates
- Support for cross-account and cross-role AWS operations
- Resource caching to minimize API calls
- Template validation and rollback capabilities
- Diff viewing before applying changes
- Integration with Kustomize for Kubernetes manifests

## Supported AWS Resources

- RDS Instances (endpoints, ports, ARNs)
- ElastiCache Clusters (endpoints, ports)
- Application Load Balancers (DNS names, ARNs, zone IDs)
- ECR Repositories (URLs, ARNs, auth tokens)
- Secrets Manager (secret values, JSON key resolution)

## Usage

### Basic Template Syntax

Templates can reference AWS resources using the following syntax:

```yaml
endpoint: {{ aws:rds:name=mydb,attr=endpoint }}
cache: {{ aws:elasticache:cluster=mycache,attr=endpoint }}
loadbalancer: {{ aws:alb:name=myalb,attr=dns }}
```

### Cross-Account Access

For cross-account resources, use the role parameter:

```yaml
endpoint: {{ aws:role=prod-readonly:rds:name=mydb,attr=endpoint }}
```

### Command Line Usage

```bash
# Show changes without applying
kustforge-wrapper -d ./k8s --aws-config ./aws-config.yaml --diff

# Apply changes and generate manifests
kustforge-wrapper -d ./k8s --aws-config ./aws-config.yaml --apply

# Use with variables
kustforge-wrapper -d ./k8s -v app_name=myapp -v replicas=3 --apply
```

## Configuration

### AWS Configuration File (aws-config.yaml)

```yaml
role_mappings:
  prod-readonly: arn:aws:iam::123456789012:role/cross-account-readonly
  
account_mappings:
  prod: "123456789012"
  staging: "987654321098"
  
profile_mappings:
  local-dev: "default"
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- AWS credentials configured
- boto3
- PyYAML
- Kustomize (optional, for Kubernetes manifest processing)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## AWS Authentication

This tool provides flexible AWS authentication methods to support both local development and production deployments:

### Local Development with AWS Profiles

For local development, you can use AWS profiles configured in your `~/.aws/credentials`:

```yaml
# aws-config.yaml
profile_mappings:
  dev: "default"
  staging: "staging-profile"
  prod: "prod-profile"
```

Usage in templates:
```yaml
# Reference resources using profile
endpoint: {{ aws:role=staging:rds:name=mydb,attr=endpoint }}
```

### Cross-Account Access with IAM Roles

For production environments, the tool supports cross-account access using IAM roles:

```yaml
# aws-config.yaml
role_mappings:
  prod-readonly: "arn:aws:iam::123456789012:role/cross-account-readonly"
  prod-admin: "arn:aws:iam::123456789012:role/cross-account-admin"

account_mappings:
  prod: "123456789012"
  staging: "987654321098"
```

Usage in templates:
```yaml
# Reference resources using explicit role ARN
endpoint: {{ aws:role=prod-readonly:rds:name=mydb,attr=endpoint }}

# Reference by account alias
secret: {{ aws:role=prod-admin:secret:name=api-key }}
```

### Authentication Flow

1. **Local Profiles**: When using profile mappings, the tool creates AWS sessions using your configured AWS profiles

2. **Role Assumption**: For cross-account access:
   - The tool first authenticates using your base credentials
   - Then uses AWS STS (Security Token Service) to assume the specified IAM role
   - Creates a temporary session with the assumed role's permissions

3. **Session Caching**: The `AWSSessionManager` caches sessions to minimize authentication overhead:
   - Sessions are cached by account ID and role name
   - Temporary credentials are valid for 1 hour
   - Sessions are automatically refreshed when expired

### Required IAM Permissions

Depending on the resources you're accessing, your IAM role needs appropriate permissions:

- RDS: `rds:DescribeDBInstances`
- ElastiCache: `elasticache:DescribeCacheClusters`
- ALB: `elasticloadbalancing:DescribeLoadBalancers`
- ECR: `ecr:DescribeRepositories`, `ecr:GetAuthorizationToken`
- Secrets Manager: `secretsmanager:GetSecretValue`

For cross-account access, you also need:
- `sts:AssumeRole` permission on your base credentials
- Trust relationship on the target role allowing assumption from your account

### Security Best Practices

1. Use the principle of least privilege when configuring IAM roles
2. Prefer role assumption over long-term access keys
3. Use separate roles for different environments
4. Regularly rotate credentials and audit access patterns
