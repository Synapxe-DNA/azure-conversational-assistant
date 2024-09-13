param principalId string
param accountName string

resource sqlRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-04-15' = {
  name: guid(resourceGroup().id, account.id, principalId)
  parent: account
  properties:{
    roleDefinitionId: '/${subscription().id}/resourceGroups/${resourceGroup().name}/providers/Microsoft.DocumentDB/databaseAccounts/${account.name}/sqlRoleDefinitions/70dead90-615e-4a87-9241-93931570e7d9'
    // roleDefinitionId: '/${subscription().id}/resourceGroups/${resourceGroup().name}/providers/Microsoft.DocumentDB/databaseAccounts/${account.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: principalId
    scope:  account.id
  }
}

resource account 'Microsoft.DocumentDB/databaseAccounts@2022-05-15' existing = {
  name: toLower(accountName)
}
