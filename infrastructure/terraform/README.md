# VeriShield AI Infrastructure

This directory contains Terraform configurations for deploying VeriShield AI infrastructure on Azure.

## Prerequisites

- Azure CLI installed and authenticated
- Terraform 1.0+
- Azure subscription with appropriate permissions

## Quick Start

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Plan the deployment:**
   ```bash
   terraform plan -var-file="terraform.tfvars"
   ```

3. **Apply the configuration:**
   ```bash
   terraform apply -var-file="terraform.tfvars"
   ```

## Variables

Create a `terraform.tfvars` file with the following variables:

```hcl
resource_group_name = "verishield-ai-prod"
location = "East US"
environment = "prod"
db_admin_username = "verishieldadmin"
db_admin_password = "YourSecurePassword123!"
apim_publisher_email = "admin@verishield.ai"
```

## Resources Created

- **Resource Group**: Central resource container
- **Virtual Network & Subnets**: Network isolation
- **Key Vault**: Secret management with RBAC
- **PostgreSQL Database**: Primary data store
- **Redis Cache**: High-performance caching
- **Blob Storage**: Media file storage
- **API Management**: Gateway with rate limiting and authentication
- **Log Analytics & Application Insights**: Monitoring and observability

## Outputs

After deployment, Terraform will output connection strings and endpoints for:

- PostgreSQL server FQDN
- Redis hostname and keys
- Storage account details
- API Management gateway URL
- Application Insights instrumentation key

## Security Considerations

- All secrets are stored in Azure Key Vault
- Network security groups restrict access
- PostgreSQL enforces SSL connections
- Redis requires TLS encryption
- API Management includes JWT validation and rate limiting

## Cost Optimization

- Uses Basic/Standard tiers for development
- Configurable scaling for production
- Reserved instances recommended for steady-state workloads

## Next Steps

After infrastructure deployment:

1. Update application configuration with Terraform outputs
2. Deploy application containers to AKS (Phase 2)
3. Configure CI/CD pipelines
4. Set up monitoring dashboards