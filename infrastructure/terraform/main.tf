# Azure Resource Manager provider configuration
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "verishield" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "VeriShield AI"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "verishield" {
  name                = "${var.resource_group_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name

  tags = {
    Environment = var.environment
  }
}

# Subnet for AKS
resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.verishield.name
  virtual_network_name = azurerm_virtual_network.verishield.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Subnet for Database
resource "azurerm_subnet" "database" {
  name                 = "database-subnet"
  resource_group_name  = azurerm_resource_group.verishield.name
  virtual_network_name = azurerm_virtual_network.verishield.name
  address_prefixes     = ["10.0.2.0/24"]
  service_endpoints    = ["Microsoft.Storage"]
}

# Network Security Group for AKS
resource "azurerm_network_security_group" "aks" {
  name                = "${var.resource_group_name}-aks-nsg"
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 101
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    Environment = var.environment
  }
}

# Azure Key Vault
resource "azurerm_key_vault" "verishield" {
  name                        = "${var.resource_group_name}-kv"
  location                    = azurerm_resource_group.verishield.location
  resource_group_name         = azurerm_resource_group.verishield.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get",
    ]

    secret_permissions = [
      "Get",
      "Set",
      "List",
      "Delete",
      "Purge"
    ]

    storage_permissions = [
      "Get",
    ]
  }

  tags = {
    Environment = var.environment
  }
}

# Azure Monitor Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "verishield" {
  name                = "${var.resource_group_name}-law"
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    Environment = var.environment
  }
}

# Azure Application Insights
resource "azurerm_application_insights" "verishield" {
  name                = "${var.resource_group_name}-ai"
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name
  application_type    = "web"

  tags = {
    Environment = var.environment
  }
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_server" "verishield" {
  name                = "${var.resource_group_name}-psql"
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name

  sku_name = "GP_Gen5_2"

  storage_mb                   = 5120
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  auto_grow_enabled            = true

  administrator_login          = var.db_admin_username
  administrator_login_password = var.db_admin_password
  version                      = "11"
  ssl_enforcement_enabled      = true

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_postgresql_database" "verishield" {
  name                = "verishield"
  resource_group_name = azurerm_resource_group.verishield.name
  server_name         = azurerm_postgresql_server.verishield.name
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "verishield" {
  name                = "${var.resource_group_name}-redis"
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name
  capacity            = 1
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  tags = {
    Environment = var.environment
  }
}

# Azure Storage Account
resource "azurerm_storage_account" "verishield" {
  name                     = "${var.resource_group_name}storage"
  resource_group_name      = azurerm_resource_group.verishield.name
  location                 = azurerm_resource_group.verishield.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_storage_container" "media" {
  name                  = "media"
  storage_account_name  = azurerm_storage_account.verishield.name
  container_access_type = "private"
}

# Azure API Management
resource "azurerm_api_management" "verishield" {
  name                = "${var.resource_group_name}-apim"
  location            = azurerm_resource_group.verishield.location
  resource_group_name = azurerm_resource_group.verishield.name
  publisher_name      = "VeriShield AI"
  publisher_email     = var.apim_publisher_email

  sku_name = "Developer_1"

  tags = {
    Environment = var.environment
  }
}

# Data source for current client config
data "azurerm_client_config" "current" {}