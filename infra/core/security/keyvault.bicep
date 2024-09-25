metadata description = 'Creates an Azure Key Vault.'
param name string
param location string = resourceGroup().location
param tags object = {}
param contentType string = 'string'
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string
param permissions object = {
  keys: [
    'Get'
    'List'
    'Update'
    'Create'
    'Import'
    'Delete'
    'Recover'
    'Backup'
    'Restore'
    'GetRotationPolicy'
    'SetRotationPolicy'
    'Rotate'
  ]
  secrets: [
    'Get'
    'List'
    'Set'
    'Delete'
    'Recover'
    'Backup'
    'Restore'
  ]
  certificates: [
    'Get'
    'List'
    'Update'
    'Create'
    'Import'
    'Delete'
    'Recover'
    'Backup'
    'Restore'
    'ManageContacts'
    'ManageIssuers'
    'GetIssuers'
    'ListIssuers'
    'SetIssuers'
    'DeleteIssuers'
  ]
}

param keyVaultReuse bool
param existingKeyVaultResourceGroupName string

param principalId string = ''

param usernameName string
#disable-next-line secure-secrets-in-params
param passwordName string
#disable-next-line secure-secrets-in-params
param secretKeyName string
@secure()
param usernameValue string
@secure()
param passwordValue string
@secure()
param secretKeyValue string


resource existingKeyVault 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = if (keyVaultReuse) {
  scope: resourceGroup(existingKeyVaultResourceGroupName)
  name: name
}

resource keyVault 'Microsoft.KeyVault/vaults@2024-04-01-preview' = if (!keyVaultReuse) {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableSoftDelete: true
    publicNetworkAccess: publicNetworkAccess
    enablePurgeProtection: true
    accessPolicies: !empty(principalId) ? [
      {
        objectId: principalId
        permissions: permissions
        tenantId: subscription().tenantId
      }
    ] : []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableRbacAuthorization: false
  }
}

resource secretUsername 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: usernameName
  tags: tags
  properties: {
    attributes: {
      enabled: true
      exp: 1735660799
    }
    contentType: contentType
    value: usernameValue
  }
}

resource secretPassword 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: passwordName
  tags: tags
  properties: {
    attributes: {
      enabled: true
      exp: 1735660799
    }
    contentType: contentType
    value: passwordValue
  }
}

resource secretKey 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: keyVault
  name: secretKeyName
  tags: tags
  properties: {
    attributes: {
      enabled: true
      exp: 1735660799
    }
    contentType: contentType
    value: secretKeyValue
  }
}

output id string = keyVaultReuse ? existingKeyVault.id : keyVault.id
output name string = keyVaultReuse ? existingKeyVault.name: keyVault.name
output endpoint string = keyVaultReuse ? existingKeyVault.properties.vaultUri: keyVault.properties.vaultUri
