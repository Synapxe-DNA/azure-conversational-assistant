metadata description = 'Creates a Cosmos DB instance.'
param name string
param location string = resourceGroup().location
param tags object = {}

param analyticalStorageConfiguration object = {
  schemaType: 'WellDefined'
}
param backupPolicy object = {
  type: 'Periodic'
  periodicModeProperties: {
    backupIntervalInMinutes: 240
    backupRetentionIntervalInHours: 8
    backupStorageRedundancy: 'Geo'
  }
}
param bypass string
param containerId string
param consistencyPolicy object = {
  defaultConsistencyLevel: 'Session'
  maxIntervalInSeconds: 5
  maxStalenessPrefix: 100
}
param databaseId string
param databaseAccountOfferType string = 'Standard'
param defaultIdentity string = 'FirstPartyIdentity'
param disableKeyBasedMetadataWriteAccess bool = false // true
param disableLocalAuth bool
param enableAnalyticalStorage bool = false
param enableAutomaticFailover bool = false
param enableBurstCapacity bool = false
param enableFreeTier bool = true
param enableMultipleWriteLocations bool = false
param enablePartitionMerge bool = false
param failoverPriority int = 0
param isZoneRedundant bool = false
param isVirtualNetworkFilterEnabled bool = false
param minimalTlsVersion string = 'Tls12'
param principalId string
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string
// param throughput int = 400
// param totalThroughputLimit int = 4000
param virtualNetworkRules array = []

param cosmosDbReuse bool
param existingCosmosDbResourceGroupName string
param existingCosmosDbAccountName string
param deployCosmosDb bool = true

resource existingAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing  = if (cosmosDbReuse && deployCosmosDb) {
  scope: resourceGroup(existingCosmosDbResourceGroupName)
  name: existingCosmosDbAccountName
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: name
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'None'
  }
  properties: {
    publicNetworkAccess: publicNetworkAccess
    enableAutomaticFailover: enableAutomaticFailover
    enableMultipleWriteLocations: enableMultipleWriteLocations
    isVirtualNetworkFilterEnabled: isVirtualNetworkFilterEnabled
    virtualNetworkRules: virtualNetworkRules
    disableKeyBasedMetadataWriteAccess: disableKeyBasedMetadataWriteAccess
    enableFreeTier: enableFreeTier
    enableAnalyticalStorage: enableAnalyticalStorage
    analyticalStorageConfiguration: analyticalStorageConfiguration
    databaseAccountOfferType: databaseAccountOfferType
    defaultIdentity: defaultIdentity
    networkAclBypass: bypass
    disableLocalAuth: disableLocalAuth
    enablePartitionMerge: enablePartitionMerge
    enableBurstCapacity: enableBurstCapacity
    minimalTlsVersion: minimalTlsVersion
    consistencyPolicy: consistencyPolicy
    locations: [
      {
        locationName: location
        failoverPriority: failoverPriority
        isZoneRedundant: isZoneRedundant
      }
    ]
    cors: []
    capabilities: [
      {
        name: 'EnableServerless' // Serverless
      }
    ]
    ipRules: []
    backupPolicy: backupPolicy
    networkAclBypassResourceIds: []
    // capacity: {
    //   totalThroughputLimit: totalThroughputLimit
    // }
  }

  resource cosmosDbBuiltInDataReader 'sqlRoleDefinitions' = {
    name: '00000000-0000-0000-0000-000000000001'
    properties: {
      roleName: 'Cosmos DB Built-in Data Reader'
      type: 'BuiltInRole'
      assignableScopes: [
        cosmos.id
      ]
      permissions: [
        {
          dataActions: [
            'Microsoft.DocumentDB/databaseAccounts/readMetadata'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/executeQuery'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/readChangeFeed'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read'
          ]
          notDataActions: []
        }
      ]
    }
  }

  resource cosmosDbBuiltInDataContributor 'sqlRoleDefinitions' = {
    name: '00000000-0000-0000-0000-000000000002'
    properties: {
      roleName: 'Cosmos DB Built-in Data Contributor'
      type: 'BuiltInRole'
      assignableScopes: [
        cosmos.id
      ]
      permissions: [
        {
          dataActions: [
            'Microsoft.DocumentDB/databaseAccounts/readMetadata'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
          ]
          notDataActions: []
        }
      ]
    }
  }

  resource cosmosDbCustomRoleDefinition 'sqlRoleDefinitions' = {
    name: '70dead90-615e-4a87-9241-93931570e7d9'
    properties: {
      roleName: 'Azure Cosmos DB Contributor'
      type: 'CustomRole'
      assignableScopes: [
        cosmos.id
      ]
      permissions: [
        {
          dataActions: [
            'Microsoft.DocumentDB/databaseAccounts/readMetadata'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
            'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
          ]
          notDataActions: []
        }
      ]
    }
  }

  resource cosmosDbCustomRole 'sqlRoleAssignments' = {
    name: '5e2ec6c0-3671-428d-b644-8308313e5566'
    properties: {
      roleDefinitionId: cosmosDbCustomRoleDefinition.id
      principalId: principalId
      scope: cosmos.id
    }
  }
}


resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmos
  name: databaseId
  properties: {
    resource: {
      id: databaseId
    }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: containerId
  properties: {
    resource: {
      id: containerId
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
      partitionKey: {
        paths: [
          '/date_time'
        ]
        kind: 'Hash'
        version: 2
      }
      uniqueKeyPolicy: {
        uniqueKeys: []
      }
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
      computedProperties: []
    }
  }

  // resource containerThroughput 'throughputSettings' = {
  //   name: 'default'
  //   properties: {
  //     resource: {
  //       throughput: throughput
  //     }
  //   }
  // }
}

output name string =  !deployCosmosDb ? '' : cosmosDbReuse ? existingAccount.name : cosmos.name
output location string =  !deployCosmosDb ? '' : cosmosDbReuse ? existingAccount.location : cosmos.location
output containerId string = container.id
output databaseId string = database.id
