output "resource_group_name" {
  value = azurerm_resource_group.verishield.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.verishield.vault_uri
}

output "postgresql_server_fqdn" {
  value = azurerm_postgresql_server.verishield.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.verishield.hostname
}

output "redis_primary_key" {
  value     = azurerm_redis_cache.verishield.primary_access_key
  sensitive = true
}

output "storage_account_name" {
  value = azurerm_storage_account.verishield.name
}

output "storage_account_key" {
  value     = azurerm_storage_account.verishield.primary_access_key
  sensitive = true
}

output "apim_gateway_url" {
  value = azurerm_api_management.verishield.gateway_url
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.verishield.workspace_id
}

output "application_insights_instrumentation_key" {
  value     = azurerm_application_insights.verishield.instrumentation_key
  sensitive = true
}

output "application_insights_connection_string" {
  value     = azurerm_application_insights.verishield.connection_string
  sensitive = true
}