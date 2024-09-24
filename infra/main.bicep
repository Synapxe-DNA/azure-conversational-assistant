targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''
@description('Id of the group to assign application roles')
param groupPrincipalId string // Set in main.parameters.json

param tenantId string = tenant().tenantId
param authTenantId string = ''

param useAuthentication bool = false
param enforceAccessControl bool = false
param enableGlobalDocuments bool = false

@description('Whether the deployment is running on GitHub Actions')
param runningOnGh string = ''

@description('Whether the deployment is running on Azure DevOps Pipeline')
param runningOnAdo string = ''

// Resource group(s) name
param resourceGroupName string = ''
param storageResourceGroupName string = ''
param openAiResourceGroupName string = ''
param searchServiceResourceGroupName string = ''
param speechResourceGroupName string = ''
param cosmosDbResourceGroupName string = ''

// Azure Log Analytics
@description('Use Application Insights for monitoring and performance tracing')
param useApplicationInsights bool // Set in main.parameters.json
param applicationInsightsName string = ''
param applicationInsightsForApimName string = ''
param applicationInsightsDashboardName string = ''
param applicationInsightsDashboardNameForApim string = ''
param logAnalyticsName string = ''
param logAnalyticsForApimName string = ''

// Azure Blob Storage
param storageAccountName string = ''
param storageResourceGroupLocation string = location
param storageContainerName string // Set in main.parameters.json
param storageSkuName string // Set in main.parameters.json

// Azure OpenAI Service
@allowed([ 'azure', 'openai', 'azure_custom' ])
param openAiHost string // Set in main.parameters.json
param isAzureOpenAiHost bool = startsWith(openAiHost, 'azure')
param deployAzureOpenAi bool = openAiHost == 'azure'
param azureOpenAiCustomUrl string = ''
param azureOpenAiApiVersion string = '2024-06-01'
@secure()
param azureOpenAiApiKey string = ''
param openAiServiceName string = ''
@description('Location for the OpenAI resource group')
@allowed([
  'canadaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'switzerlandnorth'
  'uksouth'
  'japaneast'
  'northcentralus'
  'australiaeast'
  'swedencentral'
])
@metadata({
  azd: {
    type: 'location'
  }
})
param openAiResourceGroupLocation string
param openAiSkuName string // Set in main.parameters.json

@secure()
param openAiApiKey string = ''
param openAiApiOrganization string = ''

@description('The name of the ChatGPT model.')
@allowed([ 'gpt-35-turbo', 'gpt-4o', 'gpt-4o-mini' ])
param chatGptModelName string // Set in main.parameters.json
param chatGptDeploymentName string = ''
param chatGptDeploymentCapacity int = 0 // Set in main.parameters.json
var chatGptDeploymentVersions = {
  'gpt-35-turbo': '0301'
  'gpt-4o': '2024-05-13'
  'gpt-4o-mini': '2024-07-18'
}
var chatGptDeploymentVersion = chatGptModelName == 'gpt-35-turbo' ? chatGptDeploymentVersions['gpt-35-turbo'] : chatGptModelName == 'gpt-4o' ? chatGptDeploymentVersions['gpt-4o'] : chatGptDeploymentVersions['gpt-4o-mini']
var chatGpt = {
  modelName: !empty(chatGptModelName) ? chatGptModelName : startsWith(openAiHost, 'azure') ? 'gpt-4o-mini' : 'gpt-4o-mini'
  deploymentName: !empty(chatGptDeploymentName) ? chatGptDeploymentName : 'chat'
  deploymentVersion: chatGptDeploymentVersion
  deploymentCapacity: chatGptDeploymentCapacity != 0 ? chatGptDeploymentCapacity : 30
}

@description('The name of the embedding model.')
@allowed([ 'text-embedding-ada-002', 'text-embedding-3-small', 'text-embedding-3-large' ])
param embeddingModelName string // Set in main.parameters.json
param embeddingDeploymentName string = ''
var embeddingDeploymentVersions = {
  'text-embedding-ada-002': '2'
  'text-embedding-3-small': '1'
  'text-embedding-3-large': '1'
}
var embeddingDeploymentVersion = embeddingModelName == 'text-embedding-ada-002' ? embeddingDeploymentVersions['text-embedding-ada-002'] : embeddingModelName == 'text-embedding-3-small' ? embeddingDeploymentVersions['text-embedding-3-small'] : embeddingDeploymentVersions['text-embedding-3-large']
param embeddingDeploymentCapacity int = 0
param embeddingDimensions int = 0
var embedding = {
  modelName: embeddingModelName
  deploymentName: !empty(embeddingDeploymentName) ? embeddingDeploymentName : 'embedding'
  deploymentVersion: embeddingDeploymentVersion
  deploymentCapacity: embeddingDeploymentCapacity != 0 ? embeddingDeploymentCapacity : 30
  dimensions: embeddingDimensions != 0 ? embeddingDimensions : 1536
}

// You can add more OpenAI instances by adding more objects to the openAiInstances object
// Then update the apim policy xml to include the new instances
@description('Object containing OpenAI instances. You can add more instances by adding more objects to this parameter.')
param openAiInstances object = {
  openAi1: {
    name: openAiServiceName
    location: openAiResourceGroupLocation  // Main location
    version: '-000' // Increment
  }
  openAi2: {
    name: 'openai2' // Annoyingly this must be a different value from all items in this object; can be any string
    location: 'eastus2'
    version: '-001'
  }
  // openAi3: {
  //   name: 'openai3'
  //   location: 'northcentralus'
  //   version: '-003'
  // }
}
var defaultOpenAiDeployments = [
  {
    name: chatGpt.deploymentName
    model: {
      format: 'OpenAI'
      name: chatGpt.modelName
      version: chatGpt.deploymentVersion
    }
    sku: {
      name: 'Standard'
      capacity: chatGpt.deploymentCapacity
    }
  }
  {
    name: embedding.deploymentName
    model: {
      format: 'OpenAI'
      name: embedding.modelName
      version: embedding.deploymentVersion
    }
    sku: {
      name: 'Standard'
      capacity: embedding.deploymentCapacity
    }
  }
]

var openAiDeployments = defaultOpenAiDeployments

// Azure AI Search Service
param searchServiceName string = ''
param searchServiceLocation string // Set in main.parameters.json
// The free tier does not support managed identity (required) or semantic search (optional)
@allowed([ 'free', 'basic', 'standard', 'standard2', 'standard3', 'storage_optimized_l1', 'storage_optimized_l2' ])
param searchServiceSkuName string // Set in main.parameters.json
param searchIndexName string // Set in main.parameters.json
param searchQueryLanguage string // Set in main.parameters.json
param searchQuerySpeller string // Set in main.parameters.json
param searchServiceSemanticRankerLevel string // Set in main.parameters.json
var actualSearchServiceSemanticRankerLevel = (searchServiceSkuName == 'free') ? 'disabled' : searchServiceSemanticRankerLevel
@description('Show options to use vector embeddings for searching in the app UI')
param useVectors bool // Set in main.parameters.json

// Azure Speech Service
param speechServiceName string = ''
param speechServiceLocation string // Set in main.parameters.json
param speechServiceSkuName string // Set in main.parameters.json
@description('Use speech recognition feature in browser')
param useSpeechInputBrowser bool // Set in main.parameters.json
@description('Use speech synthesis in browser')
param useSpeechOutputBrowser bool // Set in main.parameters.json
@description('Use Azure speech service for reading out text')
param useSpeechOutputAzure bool // Set in main.parameters.json

// Azure Cosmos DB
param cosmosDbName string = ''
param cosmosDbLocation string // Set in main.parameters.json
param cosmosDatabaseId string // Set in main.parameters.json
param cosmosContainerId string // Set in main.parameters.json
param cosmosDbReuse bool = false
param existingCosmosDbResourceGroupName string = ''
param existingCosmosDbAccountName string = ''

// App Service Plan
param appServicePlanName string = ''
param appServiceSkuName string // Set in main.parameters.json

// App Service
param backendServiceName string = ''
// Used for optional CORS support for alternate frontends
param allowedOrigin string = '' // should start with https://, shouldn't end with a /
param clientAppId string = ''
param serverAppId string = ''
@secure()
param serverAppSecret string = ''
param enableUnauthenticatedAccess bool = false
@secure()
param clientAppSecret string = ''
var authenticationIssuerUri = '${environment().authentication.loginEndpoint}${tenantIdForAuth}/v2.0'

// Azure API Management
param apimServiceName string = ''
param apimServiceLocation string // Set in main.parameters.json
param entraTenantId string = ''
param entraClientId string = ''
param entraAudience string = ''
param apimReuse bool = false
param existingApimResourceGroupName string = ''
param existingApimAccountName string = ''

// Data Ingestion
@description('Use Built-in integrated Vectorization feature of AI Search to vectorize and ingest documents')
param useIntegratedVectorization bool // Set in main.parameters.json
param useLocalPdfParser bool // Set in main.parameters.json
param useLocalHtmlParser bool // Set in main.parameters.json

// Azure Key Vault
param keyVaultServiceName string = ''
param keyVaultReuse bool = false
param existingKeyVaultResourceGroupName string = ''
param usernameName string = 'username'
#disable-next-line secure-secrets-in-params
param passwordName string = 'password'
#disable-next-line secure-secrets-in-params
param secretKeyName string = 'secretKey'
@secure()
param usernameValue string
@secure()
param passwordValue string
@secure()
param secretKeyValue string

// Miscellaneous
@description('Public network access value for all deployed resources')
@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'
@description('Add a private endpoints for network connectivity')
param usePrivateEndpoint bool = false
@allowed([ 'None', 'AzureServices' ])
@description('If allowedIp is set, whether azure services are allowed to bypass the storage and AI services firewall.')
param bypass string = 'AzureServices'
param identityName string = ''

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tenantIdForAuth = !empty(authTenantId) ? authTenantId : tenantId
var tags = {'azd-env-name': environmentName}

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

resource storageResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = if (!empty(storageResourceGroupName)) {
  name: !empty(storageResourceGroupName) ? storageResourceGroupName : resourceGroup.name
}

resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = if (!empty(openAiResourceGroupName)) {
  name: !empty(openAiResourceGroupName) ? openAiResourceGroupName : resourceGroup.name
}

resource searchServiceResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = if (!empty(searchServiceResourceGroupName)) {
  name: !empty(searchServiceResourceGroupName) ? searchServiceResourceGroupName : resourceGroup.name
}

resource speechResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = if (!empty(speechResourceGroupName)) {
  name: !empty(speechResourceGroupName) ? speechResourceGroupName : resourceGroup.name
}

resource cosmosDbResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = if (!empty(cosmosDbResourceGroupName)) {
  name: !empty(cosmosDbResourceGroupName) ? cosmosDbResourceGroupName : resourceGroup.name
}

// Monitor application with Azure Monitor
module monitoring 'core/monitor/monitoring.bicep' = if (useApplicationInsights) {
  name: 'monitoring'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    applicationInsightsName: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    logAnalyticsName: !empty(logAnalyticsName) ? logAnalyticsName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    // applicationInsightsDashboardName: !empty(applicationInsightsDashboardName) ? applicationInsightsDashboardName : '${abbrs.portalDashboards}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
  }
}

module applicationInsightsDashboard 'backend-dashboard.bicep' = if (useApplicationInsights) {
  name: 'application-insights-dashboard'
  scope: resourceGroup
  params: {
    name: !empty(applicationInsightsDashboardName) ? applicationInsightsDashboardName : '${abbrs.portalDashboards}${resourceToken}'
    location: location
    applicationInsightsName: useApplicationInsights ? monitoring.outputs.applicationInsightsName : ''
  }
}

module monitoringApim 'core/monitor/monitoring.bicep' = if (useApplicationInsights) {
  name: 'monitoring-apim'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    applicationInsightsName: !empty(applicationInsightsForApimName) ? applicationInsightsForApimName : '${abbrs.insightsComponents}${abbrs.apiManagementService}${resourceToken}'
    logAnalyticsName: !empty(logAnalyticsForApimName) ? logAnalyticsForApimName : '${abbrs.operationalInsightsWorkspaces}${abbrs.apiManagementService}${resourceToken}'
    // applicationInsightsDashboardName: !empty(applicationInsightsDashboardNameForApim) ? applicationInsightsDashboardNameForApim : '${abbrs.portalDashboards}${abbrs.apiManagementService}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
  }
}

module applicationInsightsDashboardForApim 'backend-dashboard.bicep' = if (useApplicationInsights) {
  name: 'application-insights-dashboard-apim'
  scope: resourceGroup
  params: {
    name: !empty(applicationInsightsDashboardNameForApim) ? applicationInsightsDashboardNameForApim : '${abbrs.portalDashboards}${abbrs.apiManagementService}${resourceToken}'
    location: location
    applicationInsightsName: useApplicationInsights ? monitoringApim.outputs.applicationInsightsName : ''
  }
}

// Azure Blob Storage
module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: storageResourceGroup
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    bypass: bypass
    sku: {
      name: storageSkuName
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: storageContainerName
        publicAccess: 'None'
      }
    ]
  }
}

// Azure OpenAI Service
module openAis 'core/ai/cognitive-services.bicep' = [for (config, i) in items(openAiInstances): {
  name: 'openai-${i}'
  scope: resourceGroup
  params: {
    name: '${abbrs.cognitiveServicesAccounts}${resourceToken}${config.value.version}'
    location: config.value.location
    tags: tags
    managedIdentityName: managedIdentity.outputs.managedIdentityName
    sku: {
      name: openAiSkuName
    }
    deploymentCapacity: chatGptDeploymentCapacity != 0 ? chatGptDeploymentCapacity : 30
    disableLocalAuth: true
    dynamicThrottlingEnabled: false
    deployments: openAiDeployments
  }
}]

// Azure AI Search Service
module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  scope: searchServiceResourceGroup
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'gptkb-${resourceToken}'
    location: !empty(searchServiceLocation) ? searchServiceLocation : location
    tags: tags
    disableLocalAuth: true
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: actualSearchServiceSemanticRankerLevel
    publicNetworkAccess: publicNetworkAccess == 'Enabled' ? 'enabled' : (publicNetworkAccess == 'Disabled' ? 'disabled' : null)
    sharedPrivateLinkStorageAccounts: usePrivateEndpoint ? [ storage.outputs.id ] : []
  }
}

module searchDiagnostics 'core/search/search-diagnostics.bicep' = if (useApplicationInsights) {
  name: 'search-diagnostics'
  scope: searchServiceResourceGroup
  params: {
    searchServiceName: searchService.outputs.name
    workspaceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
  }
}

// Azure Speech Service
module speech 'br/public:avm/res/cognitive-services/account:0.7.0' = if (useSpeechOutputAzure) {
  name: 'speech-service'
  scope: speechResourceGroup
  params: {
    name: !empty(speechServiceName) ? speechServiceName : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    kind: 'SpeechServices'
    networkAcls: {
      defaultAction: 'Allow'
    }
    customSubDomainName: !empty(speechServiceName) ? speechServiceName : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    location: !empty(speechServiceLocation) ? speechServiceLocation : location
    tags: tags
    sku: speechServiceSkuName
  }
}

// Azure Cosmos DB
module cosmosDb 'core/database/cosmos.bicep' = {
  name: 'cosmos-db'
  scope: cosmosDbResourceGroup
  params: {
    principalId: principalId
    name: !empty(cosmosDbName) ? cosmosDbName : 'cosmos-${resourceToken}'
    cosmosDbReuse: cosmosDbReuse
    existingCosmosDbResourceGroupName: existingCosmosDbResourceGroupName
    existingCosmosDbAccountName: existingCosmosDbAccountName
    databaseId: cosmosDatabaseId
    containerId: cosmosContainerId
    location: !empty(cosmosDbLocation) ? cosmosDbLocation : location
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    bypass: 'None'
    disableLocalAuth: true
  }
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: appServiceSkuName
      capacity: 1
    }
    kind: 'linux'
  }
}

// Isolation
module isolation 'network-isolation.bicep' = {
  name: 'networks'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    vnetName: '${abbrs.virtualNetworks}${resourceToken}'
    appServicePlanName: appServicePlan.outputs.name
    usePrivateEndpoint: usePrivateEndpoint
  }
}

// Azure API Management
module apim 'core/apim/apim.bicep' = {
  name: 'apim'
  scope: resourceGroup
  params: {
    name: !empty(apimServiceName) ? apimServiceName : '${abbrs.apiManagementService}${resourceToken}'
    location: !empty(apimServiceLocation) ? apimServiceLocation : location
    apimReuse: apimReuse
    existingApimResourceGroupName: existingApimResourceGroupName
    existingApimAccountName: existingApimAccountName
    tags: tags
    applicationInsightsName: monitoringApim.outputs.applicationInsightsName
    openAiUris: [for i in range(0, length(openAiInstances)): openAis[i].outputs.openAiEndpointUri]
    managedIdentityName: managedIdentity.outputs.managedIdentityName
    entraAuth: true  // keyless authentication
    clientAppId: useAuthentication ? entraClientId : null
    tenantId: useAuthentication ? entraTenantId : null
    audience: useAuthentication ? entraAudience : null
    publicNetworkAccess: publicNetworkAccess
  }
}

// The application frontend
module backend 'core/host/appservice.bicep' = {
  name: 'web'
  scope: resourceGroup
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.11'
    appCommandLine: 'python3 -m gunicorn main:app'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    virtualNetworkSubnetId: isolation.outputs.appSubnetId
    publicNetworkAccess: publicNetworkAccess
    allowedOrigins: [ allowedOrigin ]
    clientAppId: clientAppId
    serverAppId: serverAppId
    enableUnauthenticatedAccess: enableUnauthenticatedAccess
    clientSecretSettingName: !empty(clientAppSecret) ? 'AZURE_CLIENT_APP_SECRET' : ''
    authenticationIssuerUri: authenticationIssuerUri
    use32BitWorkerProcess: appServiceSkuName == 'F1'
    alwaysOn: appServiceSkuName != 'F1'
    appSettings: {
      // Azure Blob Storage
      AZURE_STORAGE_ACCOUNT: storage.outputs.name
      AZURE_STORAGE_CONTAINER: storageContainerName
      AZURE_STORAGE_SKU: storageSkuName
      // Azure OpenAI Service
      // Shared by all OpenAI deployments
      OPENAI_HOST: openAiHost
      AZURE_OPENAI_CHATGPT_MODEL: chatGpt.modelName
      AZURE_OPENAI_EMB_MODEL_NAME: embedding.modelName
      AZURE_OPENAI_EMB_DIMENSIONS: embedding.dimensions
      // Specific to Azure OpenAI
      AZURE_OPENAI_SERVICE: isAzureOpenAiHost && deployAzureOpenAi ? openAis[0].outputs.openAiName : ''
      AZURE_OPENAI_CHATGPT_DEPLOYMENT: isAzureOpenAiHost ? chatGpt.deploymentName : ''
      AZURE_OPENAI_EMB_DEPLOYMENT: isAzureOpenAiHost ? embedding.deploymentName : ''
      AZURE_OPENAI_API_VERSION: isAzureOpenAiHost ? azureOpenAiApiVersion : '2024-06-01'
      AZURE_OPENAI_API_KEY: azureOpenAiApiKey
      AZURE_OPENAI_CUSTOM_URL: azureOpenAiCustomUrl
      AZURE_OPENAI_SKU: isAzureOpenAiHost ? openAiSkuName : ''
      AZURE_OPENAI_NUMBER_DEPLOYMENTS: length(openAiInstances)
      // Used only with non-Azure OpenAI deployments
      OPENAI_API_KEY: openAiApiKey
      OPENAI_ORGANIZATION: openAiApiOrganization
      // Azure AI Search Service
      AZURE_SEARCH_LOCATION: searchService.outputs.location
      AZURE_SEARCH_SERVICE: searchService.outputs.name
      AZURE_SEARCH_INDEX: searchIndexName
      AZURE_SEARCH_QUERY_LANGUAGE: searchQueryLanguage
      AZURE_SEARCH_QUERY_SPELLER: searchQuerySpeller
      AZURE_SEARCH_SEMANTIC_RANKER: actualSearchServiceSemanticRankerLevel
      AZURE_SEARCH_SERVICE_SKU: searchServiceSkuName
      USE_VECTORS: useVectors
      // Azure Speech Service
      AZURE_SPEECH_SERVICE_ID: useSpeechOutputAzure ? speech.outputs.resourceId : ''
      AZURE_SPEECH_SERVICE_LOCATION: useSpeechOutputAzure ? speech.outputs.location : ''
      AZURE_SPEECH_SERVICE: useSpeechOutputAzure ? speech.outputs.name : ''
      AZURE_SPEECH_SERVICE_SKU: useSpeechOutputAzure ? speechServiceSkuName : ''
      USE_SPEECH_INPUT_BROWSER: useSpeechInputBrowser
      USE_SPEECH_OUTPUT_BROWSER: useSpeechOutputBrowser
      USE_SPEECH_OUTPUT_AZURE: useSpeechOutputAzure
      // Azure Cosmos DB
      AZURE_COSMOS_DB_NAME: !empty(cosmosDbName) ? cosmosDbName : cosmosDb.outputs.name
      AZURE_COSMOS_DB_LOCATION: cosmosDb.outputs.location
      AZURE_DATABASE_ID: !empty(cosmosDatabaseId) ? cosmosDatabaseId : cosmosDb.outputs.databaseId
      AZURE_CONTAINER_ID: !empty(cosmosContainerId) ? cosmosContainerId : cosmosDb.outputs.containerId
      // Azure API Management
      AZURE_APIM_SERVICE_NAME: !empty(apimServiceName) ? apimServiceName : apim.outputs.apimName
      APIM_AOI_PATH: apim.outputs.apimOpenAiApiPath
      APIM_GATEWAY_URL: apim.outputs.apimGatewayUrl
      APIM_MANAGED_IDENTITY_PRINCIPAL_ID: managedIdentity.outputs.managedIdentityPrincipalId
      // Optional login and document level access control system
      AZURE_USE_AUTHENTICATION: useAuthentication
      AZURE_ENFORCE_ACCESS_CONTROL: enforceAccessControl
      AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS: enableGlobalDocuments
      AZURE_ENABLE_UNAUTHENTICATED_ACCESS: enableUnauthenticatedAccess
      AZURE_SERVER_APP_ID: serverAppId
      AZURE_SERVER_APP_SECRET: serverAppSecret
      AZURE_CLIENT_APP_ID: clientAppId
      AZURE_CLIENT_APP_SECRET: clientAppSecret
      AZURE_TENANT_ID: tenantId
      AZURE_AUTH_TENANT_ID: tenantIdForAuth
      AZURE_AUTHENTICATION_ISSUER_URI: authenticationIssuerUri
      // CORS support, for frontends on other hosts
      ALLOWED_ORIGIN: allowedOrigin
      // Data Ingestion
      USE_FEATURE_INT_VECTORIZATION :useIntegratedVectorization
      USE_LOCAL_PDF_PARSER: useLocalPdfParser
      USE_LOCAL_HTML_PARSER: useLocalHtmlParser
      APPLICATIONINSIGHTS_CONNECTION_STRING: useApplicationInsights ? monitoring.outputs.applicationInsightsConnectionString : ''
      APPLICATIONINSIGHTS_FOR_APIM_CONNECTION_STRING: useApplicationInsights ? monitoringApim.outputs.applicationInsightsConnectionString : ''
      // Azure Key Vault
      AZURE_KEY_VAULT_ID: keyVault.outputs.id
      AZURE_KEY_VAULT_NAME: !empty(keyVaultServiceName) ? keyVaultServiceName : '${abbrs.keyVaultVaults}${resourceToken}'
      AZURE_KEY_VAULT_ENDPOINT: keyVault.outputs.endpoint
    }
  }
}

// Azure Key Vault
module keyVault 'core/security/keyvault.bicep' = {
  name: 'keyvault'
  scope: resourceGroup
  params: {
    name: !empty(keyVaultServiceName) ? keyVaultServiceName : '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    keyVaultReuse: keyVaultReuse
    existingKeyVaultResourceGroupName: existingKeyVaultResourceGroupName
    publicNetworkAccess: publicNetworkAccess
    tags: tags
    principalId: principalId
    usernameName: usernameName
    passwordName: passwordName
    usernameValue: usernameValue
    passwordValue: passwordValue
    secretKeyName: secretKeyName
    secretKeyValue: secretKeyValue
  }
}

// USER ROLES
var principalType = empty(runningOnGh) && empty(runningOnAdo) ? 'User' : 'ServicePrincipal'

// Azure Blob Storage Roles
module storageRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: principalType
  }
}

module storageContribRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: principalType
  }
}

// Azure OpenAI Service Role
module openAiRoleUser 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  scope: openAiResourceGroup
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: principalType
  }
}

// Azure AI Search Service Roles
module searchRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: principalType
  }
}

module searchContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: principalType
  }
}

module searchSvcContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-svccontrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: principalType
  }
}

// Azure Speech Service Role
module speechRoleUser 'core/security/role.bicep' = {
  scope: speechResourceGroup
  name: 'speech-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'f2dc8367-1007-4938-bd23-fe263f013447'
    principalType: principalType
  }
}

// SYSTEM IDENTITIES

// Azure Blob Storage System Identities
module storageRoleBackend 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleSearchService 'core/security/role.bicep' = if (useIntegratedVectorization) {
  scope: storageResourceGroup
  name: 'storage-role-searchservice'
  params: {
    principalId: searchService.outputs.principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

// Azure OpenAI Service System Identities
module openAiRoleBackend 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  scope: openAiResourceGroup
  name: 'openai-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}


module openAiRoleSearchService 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi && useIntegratedVectorization) {
  scope: openAiResourceGroup
  name: 'openai-role-searchservice'
  params: {
    principalId: searchService.outputs.principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

// Azure AI Search Service System Identities
// Used to issue search queries
// https://learn.microsoft.com/azure/search/search-security-rbac
module searchRoleBackend 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

// Used to read index definitions (required when using authentication)
// https://learn.microsoft.com/azure/search/search-security-rbac
module searchReaderRoleBackend 'core/security/role.bicep' = if (useAuthentication) {
  scope: searchServiceResourceGroup
  name: 'search-reader-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
    principalType: 'ServicePrincipal'
  }
}

// Azure Speech Service System Identity
module speechRoleBackend 'core/security/role.bicep' = {
  scope: speechResourceGroup
  name: 'speech-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: 'f2dc8367-1007-4938-bd23-fe263f013447'
    principalType: 'ServicePrincipal'
  }
}

// Azure Cosmos DB System Identity
module cosmosDbRoleBackend 'core/security/cosmos-access.bicep' = {
  scope: cosmosDbResourceGroup
  name: 'cosmosdb-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    accountName: cosmosDb.outputs.name
  }
}

module managedIdentity 'core/security/managed-identity.bicep' = {
  name: 'managed-identity'
  scope: resourceGroup
  params: {
    name: !empty(identityName) ? identityName : '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
    location: location
    tags: tags
  }
}

// Assign the Cognitive Services User role to the user-defined managed identity used by workloads
module cognitiveServicesUserRoleAssignment 'core/security/role.bicep' = {
  scope: openAiResourceGroup
  name: 'cognitive-services-user-role-assignment'
  params: {
    principalId: managedIdentity.outputs.managedIdentityPrincipalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

// Azure Key Vault
module backendKeyVaultAccess 'core/security/keyvault-access.bicep' = {
  name: 'appservice-keyvault-access'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    principalId: backend.outputs.identityPrincipalId
  }
}

module groupKeyVaultAccess 'core/security/keyvault-access.bicep' = {
  name: 'group-keyvault-access'
  scope: resourceGroup
  params: {
    keyVaultName: keyVault.outputs.name
    principalId: groupPrincipalId
  }
}

// var environmentData = environment()

// var openAiPrivateEndpointConnection = (isAzureOpenAiHost && deployAzureOpenAi) ? [{
//   groupId: 'account'
//   dnsZoneName: 'privatelink.openai.azure.com'
//   resourceIds: openAi.outputs.resourceId
// }] : []

// var otherPrivateEndpointConnections = usePrivateEndpoint ? [
//   {
//     groupId: 'blob'
//     dnsZoneName: 'privatelink.blob.${environmentData.suffixes.storage}'
//     resourceIds: storage.outputs.id
//   }
//   {
//     groupId: 'searchService'
//     dnsZoneName: 'privatelink.search.windows.net'
//     resourceIds: [ searchService.outputs.id ]
//   }
//   {
//     groupId: 'sites'
//     dnsZoneName: 'privatelink.azurewebsites.net'
//     resourceIds: [ backend.outputs.id ]
//   }
// ] : []

// var privateEndpointConnections = concat(otherPrivateEndpointConnections, openAiPrivateEndpointConnection)

// module privateEndpoints 'private-endpoints.bicep' = if (usePrivateEndpoint) {
//   name: 'privateEndpoints'
//   scope: resourceGroup
//   params: {
//     location: location
//     tags: tags
//     resourceToken: resourceToken
//     privateEndpointConnections: privateEndpointConnections
//     applicationInsightsId: useApplicationInsights ? monitoring.outputs.applicationInsightsId : ''
//     logAnalyticsWorkspaceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
//     vnetName: isolation.outputs.vnetName
//     vnetPeSubnetName: isolation.outputs.backendSubnetId
//   }
// }

output AZURE_LOCATION string = location
output AZURE_PRINCIPAL_ID string = principalId
output AZURE_GROUP_PRINCIPAL_ID string = groupPrincipalId
output AZURE_TENANT_ID string = tenantId
output AZURE_AUTH_TENANT_ID string = authTenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name

// Azure Blob Storage
output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_CONTAINER string = storageContainerName
output AZURE_STORAGE_RESOURCE_GROUP string = storageResourceGroup.name
output AZURE_STORAGE_SKU string = storageSkuName

// Azure OpenAI Service
output OPENAI_HOST string = openAiHost
output AZURE_OPENAI_LOCATION string = openAiResourceGroupLocation
output AZURE_OPENAI_CHATGPT_MODEL string = chatGpt.modelName
output AZURE_OPENAI_CHATGPT_DEPLOYMENT string = isAzureOpenAiHost ? chatGpt.deploymentName : ''
output AZURE_OPENAI_CHATGPT_DEPLOYMENT_VERSION string = chatGpt.deploymentVersion
output AZURE_OPENAI_EMB_MODEL_NAME string = embedding.modelName
output AZURE_OPENAI_EMB_DEPLOYMENT string = isAzureOpenAiHost ? embedding.deploymentName : ''
output AZURE_OPENAI_EMB_DEPLOYMENT_VERSION string = embedding.deploymentVersion
output AZURE_OPENAI_SERVICE string = isAzureOpenAiHost && deployAzureOpenAi ? openAis[0].outputs.openAiName : ''
output AZURE_OPENAI_API_VERSION string = isAzureOpenAiHost ? azureOpenAiApiVersion : '2024-06-01'
output AZURE_OPENAI_SKU string = isAzureOpenAiHost ? openAiSkuName : ''
output AZURE_OPENAI_NUMBER_DEPLOYMENTS int = length(openAiInstances)

// Azure AI Search Service
output AZURE_SEARCH_LOCATION string = searchService.outputs.location
output AZURE_SEARCH_SERVICE string = searchService.outputs.name
output AZURE_SEARCH_INDEX string = searchIndexName
output AZURE_SEARCH_QUERY_LANGUAGE string = searchQueryLanguage
output AZURE_SEARCH_QUERY_SPELLER string = searchQuerySpeller
output AZURE_SEARCH_SEMANTIC_RANKER string = actualSearchServiceSemanticRankerLevel
output AZURE_SEARCH_SERVICE_ASSIGNED_USERID string = searchService.outputs.principalId
output AZURE_SEARCH_SERVICE_SKU string = searchServiceSkuName

// Azure Speech Service
output AZURE_SPEECH_SERVICE_LOCATION string = useSpeechOutputAzure ? speech.outputs.location : ''
output AZURE_SPEECH_SERVICE string = useSpeechOutputAzure ? speech.outputs.name : ''
output AZURE_SPEECH_SERVICE_SKU string = useSpeechOutputAzure ? speechServiceSkuName : ''
output AZURE_SPEECH_SERVICE_ID string = useSpeechOutputAzure ? speech.outputs.resourceId : ''
output USE_SPEECH_INPUT_BROWSER bool = useSpeechInputBrowser
output USE_SPEECH_OUTPUT_BROWSER bool = useSpeechOutputBrowser
output USE_VECTORS bool = useVectors
output USE_SPEECH_OUTPUT_AZURE bool = useSpeechOutputAzure

// Azure Cosmos DB
output AZURE_COSMOS_DB_NAME string = !empty(cosmosDbName) ? cosmosDbName : cosmosDb.outputs.name
output AZURE_COSMOS_DB_LOCATION string = cosmosDb.outputs.location
output AZURE_DATABASE_ID string = !empty(cosmosDatabaseId) ? cosmosDatabaseId : cosmosDb.outputs.databaseId
output AZURE_CONTAINER_ID string = !empty(cosmosContainerId) ? cosmosContainerId : cosmosDb.outputs.containerId

// Azure API Management
output AZURE_APIM_SERVICE_NAME string = !empty(apimServiceName) ? apimServiceName : apim.outputs.apimName
output AZURE_APIM_LOCATION string = apim.outputs.location
output APIM_AOI_PATH string = apim.outputs.apimOpenAiApiPath
output APIM_GATEWAY_URL string = apim.outputs.apimGatewayUrl
output APIM_MANAGED_IDENTITY_PRINCIPAL_ID string = managedIdentity.outputs.managedIdentityPrincipalId

// App Service Plan
output AZURE_APP_SERVICE_PLAN string = !empty(appServicePlanName) ? appServicePlanName : appServicePlan.outputs.name
output AZURE_APP_SERVICE_SKU string = appServiceSkuName

// Data Ingestion
output USE_FEATURE_INT_VECTORIZATION bool = useIntegratedVectorization
output USE_LOCAL_PDF_PARSER bool = useLocalPdfParser
output USE_LOCAL_HTML_PARSER bool = useLocalHtmlParser

// Logging
output APPLICATIONINSIGHTS_CONNECTION_STRING string = useApplicationInsights ? monitoring.outputs.applicationInsightsConnectionString : ''
output APPLICATIONINSIGHTS_FOR_APIM_CONNECTION_STRING string = useApplicationInsights ? monitoringApim.outputs.applicationInsightsConnectionString : ''

// Azure Key Vault
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.endpoint

output AZURE_USE_AUTHENTICATION bool = useAuthentication

output BACKEND_URI string = backend.outputs.uri
