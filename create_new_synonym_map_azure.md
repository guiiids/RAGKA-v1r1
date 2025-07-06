<!--
This document provides instructions to create or update a synonym map in Azure Cognitive Search using the Azure CLI.

The process involves:
1. Preparing a synonym map JSON file that defines your synonyms.
2. Retrieving the Search Service API key for authentication.
3. Using the `az rest` command to send a PUT request to the Azure Search REST API endpoint to create or update the synonym map.
4. The synonym map JSON file (e.g., `synonymsCommunity.json`) should be present in the working directory and contains the synonym definitions.

Example of a synonym map JSON file (`synonymsCommunity.json`):
```json
{
  "name": "synonyms-community",
  "format": "solr",
  "synonyms": "USA, United States, United States of America\nNY, New York"
}
```

Usage:
- Replace the resource group and service name with your Azure Search service details.
- Replace `<search_service_primary_key>` with the actual API key retrieved in step 2.
- Replace the JSON file name in the `--body` parameter with your synonym map JSON file.

This allows Azure Cognitive Search to use custom synonym mappings to improve search relevance.
-->

# Get the Search Service API Key
az search admin-key show \
  --resource-group rg-sbx-19-switzerlandnorth-usr-capozzol \
  --service-name capozzol01searchservice

# Build the URL

To create a new synonym map, you just:

- Pick a unique name — let’s say `synonyms-community-second-map-example`

- Craft the full URL manually:
`https://capozzol01searchservice.search.windows.net/synonymmaps/synonyms-community-second-map-example?api-version=2023-11-01`

- Add the above to the `--uri` field in the step below.

# Change the line `--body "@synonymsCommunity.json"` with the name of json file in the root folder of your working directory

az rest --method put \
  --uri "https://capozzol01searchservice.search.windows.net/synonymmaps/synonyms-community?api-version=2023-11-01" \
  --headers "Content-Type=application/json" "api-key=<search_service_primary_key>" \
  --body "@synonymsCommunity.json"