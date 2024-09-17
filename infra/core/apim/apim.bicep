metadata description = 'Creates an Azure API Management.'
param name string
param location string = resourceGroup().location
param tags object = {}

param applicationInsightsName string
param audience string = 'https://cognitiveservices.azure.com/.default'
param clientAppId string = ' '
param entraAuth bool = true
param managedIdentityName string
param openAiUris array
@minLength(1)
param publisherName string = 'n/a'
@minLength(1)
param publisherEmail string = 'noreply@microsoft.com'
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string
param sku string = 'Developer'
param skuCount int = 1
param tenantId string = tenant().tenantId

param apimReuse bool
param existingApimResourceGroupName string
param existingApimAccountName string
param deployApim bool = true

var openAiApiBackendId = 'openai-backend'
var openAiApiUamiNamedValue = 'uami-client-id'
var openAiApiEntraNamedValue = 'entra-auth'
var openAiApiClientNamedValue = 'client-id'
var openAiApiTenantNamedValue = 'tenant-id'
var openAiApiAudienceNamedValue = 'audience'

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-07-31-preview' existing = {
  name: managedIdentityName
}

resource existingAccount 'Microsoft.ApiManagement/service@2023-09-01-preview' existing  = if (apimReuse && deployApim) {
  scope: resourceGroup(existingApimResourceGroupName)
  name: existingApimAccountName
}

resource apimService 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
    capacity: (sku == 'Consumption') ? 0 : ((sku == 'Developer') ? 1 : skuCount)
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
    notificationSenderEmail: 'apimgmt-noreply@mail.windowsazure.com'
    hostnameConfigurations: [
      {
        type: 'Proxy'
        hostName: '${name}.azure-api.net'
        negotiateClientCertificate: false
        defaultSslBinding: true
        certificateSource: 'BuiltIn'
      }
    ]
    // Custom properties are not supported for Consumption SKU
    customProperties: sku == 'Consumption' ? {} : {
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Ssl30': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Protocols.Server.Http2': 'False'
    }
    virtualNetworkType: 'None'
    disableGateway: false
    natGatewayState: 'Unsupported'
    apiVersionConstraint: {}
    publicNetworkAccess: publicNetworkAccess
    legacyPortalStatus: 'Disabled'
    developerPortalStatus: 'Enabled'
  }
}

resource apimOpenAiApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  name: 'azure-openai-service-api'
  parent: apimService
  properties: {
    path: 'openai'
    apiRevision: '1'
    displayName: 'Azure OpenAI Service API'
    subscriptionRequired: entraAuth ? false : true
    serviceUrl: 'https://microsoft.com/openai'
    subscriptionKeyParameterNames: {
      header: 'api-key'
      query: 'subscription-key'
    }
    format: 'openapi+json'
    value: loadJsonContent('./openai/inference.json')
    protocols: [
      'https'
    ]
    authenticationSettings: {
      oAuth2AuthenticationSettings: []
      openidAuthenticationSettings: []
    }
    isCurrent: true
  }
}

resource openAiBackends 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = [for (openAiUri, i) in openAiUris: {
  name: '${openAiApiBackendId}-${i}'
  parent: apimService
  properties: {
    description: openAiApiBackendId
    url: openAiUri
    protocol: 'http'
    tls: {
      validateCertificateChain: true
      validateCertificateName: true
    }
  }
}]

resource apimOpenAiApiUamiNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  name: openAiApiUamiNamedValue
  parent: apimService
  properties: {
    displayName: openAiApiUamiNamedValue
    secret: true
    value: managedIdentity.properties.clientId
  }
}

resource apiopenAiApiEntraNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  name: openAiApiEntraNamedValue
  parent: apimService
  properties: {
    displayName: openAiApiEntraNamedValue
    secret: false
    #disable-next-line BCP036
    value: entraAuth
  }
}

resource apiopenAiApiClientNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  name: openAiApiClientNamedValue
  parent: apimService
  properties: {
    displayName: openAiApiClientNamedValue
    secret: true
    value: clientAppId
  }
}

resource apiopenAiApiTenantNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  name: openAiApiTenantNamedValue
  parent: apimService
  properties: {
    displayName: openAiApiTenantNamedValue
    secret: true
    value: tenantId
  }
}

resource apimOpenAiApiAudienceiNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' =  {
  name: openAiApiAudienceNamedValue
  parent: apimService
  properties: {
    displayName: openAiApiAudienceNamedValue
    secret: true
    value: audience
  }
}

resource openaiApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-09-01-preview' =  {
  name: 'policy'
  parent: apimOpenAiApi
  properties: {
    value: loadTextContent('./policies/api_policy.xml')
    format: 'rawxml'
  }
  dependsOn: [
    openAiBackends
    apiopenAiApiClientNamedValue
    apiopenAiApiEntraNamedValue
    apimOpenAiApiAudienceiNamedValue
    apiopenAiApiTenantNamedValue
  ]
}

resource apimLogger 'Microsoft.ApiManagement/service/loggers@2023-09-01-preview' = {
  name: 'appinsights-logger'
  parent: apimService
  properties: {
    credentials: {
      instrumentationKey: applicationInsights.properties.InstrumentationKey
    }
    description: 'Logger to Azure Application Insights'
    isBuffered: false
    loggerType: 'applicationInsights'
    resourceId: applicationInsights.id
  }
}

resource apimUser 'Microsoft.ApiManagement/service/users@2020-06-01-preview' = {
  parent: apimService
  name: 'myUser'
  properties: {
    firstName: 'My'
    lastName: 'User'
    email: 'myuser@example.com'
    state: 'active'
  }
}

resource apimSubscription 'Microsoft.ApiManagement/service/subscriptions@2020-06-01-preview' = {
  parent: apimService
  name: 'mySubscription'
  properties: {
    displayName: 'My Subscription'
    state: 'active'
    allowTracing: true
    scope: '/apis/${apimOpenAiApi.name}'
  }
}

@description('The name of the deployed API Management service.')
output apimName string = !deployApim ? '' : apimReuse ? existingAccount.name : apimService.name

@description('The location of the deployed API Management service.')
output location string =  !deployApim ? '' : apimReuse ? existingAccount.location : apimService.location

@description('The path for the OpenAI API in the deployed API Management service.')
output apimOpenAiApiPath string = apimOpenAiApi.properties.path

@description('Gateway URL for the deployed API Management resource.')
output apimGatewayUrl string = apimService.properties.gatewayUrl
