param name string
param location string = resourceGroup().location
param tags object = {}
param managedIdentityName string = ''
param deployments array = []
param kind string = 'OpenAI'
param sku object = {
  name: 'S0'
}
param deploymentCapacity int = 2

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-07-31-preview' existing = {
  name: managedIdentityName
}

resource account 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': name })
  kind: kind
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    customSubDomainName: name
  }
  sku: sku
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [for deployment in deployments: {
  parent: account
  name: deployment.name
  properties: {
    model: deployment.model
    raiPolicyName: deployment.?raiPolicyName ?? null
  }
  sku: deployment.?sku ?? {
    name: 'Standard'
    capacity: deploymentCapacity
  }
}]

output openAiName string = account.name
output openAiEndpointUri string = '${account.properties.endpoint}openai/'
