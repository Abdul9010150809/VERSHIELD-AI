# API Management API Definition
resource "azurerm_api_management_api" "verishield" {
  name                = "verishield-api"
  resource_group_name = azurerm_resource_group.verishield.name
  api_management_name = azurerm_api_management.verishield.name
  revision            = "1"
  display_name        = "VeriShield AI API"
  path                = "api"
  protocols           = ["https"]

  subscription_required = false

  import {
    content_format = "openapi"
    content_value  = file("../../docs/api/openapi.yaml")
  }
}

# API Management Product
resource "azurerm_api_management_product" "verishield" {
  product_id            = "verishield-product"
  api_management_name   = azurerm_api_management.verishield.name
  resource_group_name   = azurerm_resource_group.verishield.name
  display_name          = "VeriShield AI"
  description           = "Deepfake detection API for financial transactions"
  subscription_required = true
  approval_required     = false
  published             = true
}

# Product API Association
resource "azurerm_api_management_product_api" "verishield" {
  api_name            = azurerm_api_management_api.verishield.name
  product_id          = azurerm_api_management_product.verishield.product_id
  api_management_name = azurerm_api_management.verishield.name
  resource_group_name = azurerm_resource_group.verishield.name
}

# Rate Limiting Policy
resource "azurerm_api_management_api_policy" "rate_limit" {
  api_name            = azurerm_api_management_api.verishield.name
  api_management_name = azurerm_api_management.verishield.name
  resource_group_name = azurerm_resource_group.verishield.name

  xml_content = <<XML
<policies>
  <inbound>
    <rate-limit calls="100" renewal-period="60" />
    <quota calls="1000" renewal-period="3600" />
    <validate-jwt header-name="Authorization" failed-validation-httpcode="401" failed-validation-error-message="Unauthorized">
      <openid-config url="https://login.microsoftonline.com/common/.well-known/openid_configuration" />
      <required-claims>
        <claim name="aud">
          <value>your-api-audience</value>
        </claim>
      </required-claims>
    </validate-jwt>
  </inbound>
  <backend>
    <forward-request />
  </backend>
  <outbound />
  <on-error />
</policies>
XML
}

# API Version Set
resource "azurerm_api_management_api_version_set" "verishield" {
  name                = "verishield-api-versions"
  resource_group_name = azurerm_resource_group.verishield.name
  api_management_name = azurerm_api_management.verishield.name
  display_name        = "VeriShield API"
  versioning_scheme   = "Segment"
}