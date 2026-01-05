variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "verishield-ai-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "db_admin_username" {
  description = "PostgreSQL administrator username"
  type        = string
  default     = "verishieldadmin"
}

variable "db_admin_password" {
  description = "PostgreSQL administrator password"
  type        = string
  sensitive   = true
}

variable "apim_publisher_email" {
  description = "API Management publisher email"
  type        = string
  default     = "admin@verishield.ai"
}