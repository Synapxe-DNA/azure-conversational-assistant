output=$(azd env get-values)

while IFS= read -r line; do
  name=$(echo "$line" | cut -d '=' -f 1)
  value=$(echo "$line" | cut -d '=' -f 2 | sed 's/^\"//;s/\"$//')
  export "$name"="$value"
done <<< "$output"

echo "Environment variables set."

roles=(
    "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" # Cognitive Services OpenAI User
    "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1" # Storage Blob Data Reader
    "ba92f5b4-2d11-453d-a403-e96b0029c9fe" # Storage Blob Data Contributor
    "1407120a-92aa-4202-b7e9-c0e197c71c8f" # Search Index Data Reader
    "8ebe5a00-799e-43f5-93ac-243d3dce84a7" # Search Index Data Contributor
    "f2dc8367-1007-4938-bd23-fe263f013447" # Cognitive Services Speech User
)

if [ -z "$AZURE_RESOURCE_GROUP" ]; then
    export AZURE_RESOURCE_GROUP="rg-$AZURE_ENV_NAME"
    azd env set AZURE_RESOURCE_GROUP "$AZURE_RESOURCE_GROUP"
fi

for role in "${roles[@]}"; do
    az role assignment create \
        --role "$role" \
        --assignee-object-id "$AZURE_GROUP_PRINCIPAL_ID" \
        --scope /subscriptions/"$AZURE_SUBSCRIPTION_ID"/resourceGroups/"$AZURE_RESOURCE_GROUP" \
        --assignee-principal-type Group
done

az cosmosdb sql role assignment create \
	--account-name "$AZURE_COSMOS_DB_NAME" \
	--resource-group "$AZURE_RESOURCE_GROUP" \
	--scope /subscriptions/"$AZURE_SUBSCRIPTION_ID"/resourceGroups/"$AZURE_RESOURCE_GROUP"/providers/Microsoft.DocumentDB/databaseAccounts/"$AZURE_COSMOS_DB_NAME" \
	--principal-id "$AZURE_GROUP_PRINCIPAL_ID" \
	--role-definition-id "70dead90-615e-4a87-9241-93931570e7d9"  # Custom role: Cosmos DB Built-in Data Reader + Cosmos DB Built-in Data Contributor
