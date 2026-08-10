## cloud.azure_ops.rag_pipeline playbook

A playbook to deploy a RAG (Retrieval-Augmented Generation) pipeline on Azure using Azure AI Search and Azure OpenAI.

This reference architecture automates the full RAG stack: storage for source documents, Azure AI Search for indexing and retrieval, and Azure OpenAI for embeddings and chat completion.

### Use Cases

* **Enterprise knowledge base** — Index internal documents and serve answers via Azure OpenAI
* **Customer support automation** — Search product documentation and generate contextual responses
* **Compliance document Q&A** — Query regulatory documents with retrieval-augmented generation

### Prerequisites

* Azure subscription with sufficient quota
* `azure.azcollection` >= 3.9.0 installed
* Azure credentials configured (service principal, managed identity, or CLI auth)
* The following Azure resource providers must be registered on the subscription:
  - `Microsoft.Storage`
  - `Microsoft.Search`
  - `Microsoft.CognitiveServices`

Variables
--------------

###### Common
--------------

* **azure_resource_group**: (Required) Resource group for the RAG pipeline resources.
* **azure_region**: An Azure location for the resources. Default: `eastus`
* **operation**: Operation to perform. Valid values are `create`, `delete`. Default: `create`

--------------
###### Storage
--------------

* **azure_storage_account_name**: Name of the storage account. Default: `{{ azure_resource_group | regex_replace('[^a-z0-9]', '') }}storage`
* **azure_storage_container_name**: Name of the blob container for documents. Default: `documents`

--------------
###### AI Search
--------------

* **azure_ai_search_name**: Name of the AI Search service. Default: `{{ azure_resource_group }}-search`
* **azure_ai_search_sku**: Pricing tier for AI Search. Default: `basic`

--------------
###### OpenAI
--------------

* **azure_openai_account_name**: Name of the Azure OpenAI account. Default: `{{ azure_resource_group }}-openai`
* **azure_openai_embedding_model**: Embedding model name. Default: `text-embedding-ada-002`
* **azure_openai_embedding_model_version**: Embedding model version. Default: `2`
* **azure_openai_embedding_deployment_name**: Deployment name for the embedding model. Default: `embedding-deployment`
* **azure_openai_embedding_capacity**: Capacity units for the embedding deployment. Default: `1`
* **azure_openai_chat_model**: Chat completion model name. Default: `gpt-4o`
* **azure_openai_chat_model_version**: Chat model version. Default: `2024-11-20`
* **azure_openai_chat_deployment_name**: Deployment name for the chat model. Default: `chat-deployment`
* **azure_openai_chat_capacity**: Capacity units for the chat deployment. Default: `1`

--------------
###### Search Index
--------------

* **azure_ai_search_index_name**: Name of the search index. Default: `rag-index`
* **azure_ai_search_datasource_name**: Name of the data source connection. Default: `rag-datasource`
* **azure_ai_search_indexer_name**: Name of the indexer. Default: `rag-indexer`
* **azure_ai_search_skillset_name**: Name of the skillset. Default: `rag-skillset`

### Usage

#### Create RAG Pipeline

```bash
ansible-playbook cloud.azure_ops.rag_pipeline \
  -e azure_resource_group=my-rag-rg \
  -e azure_region=eastus
```

#### Delete RAG Pipeline

```bash
ansible-playbook cloud.azure_ops.rag_pipeline \
  -e azure_resource_group=my-rag-rg \
  -e operation=delete
```

### Security Best Practices

The playbook deploys with system-assigned managed identity enabled on AI Search and OpenAI for demo simplicity. For production deployments, consider:

* **RBAC Role Assignments**: Assign `Storage Blob Data Reader` to the AI Search managed identity on the storage account. Assign `Cognitive Services OpenAI User` to the AI Search managed identity on the OpenAI account. This eliminates the need for connection strings and API keys.
* **Private Endpoints**: Replace public network access with private endpoints for AI Search, OpenAI, and Storage Account. Create private DNS zones for each service.
* **Network Isolation**: Deploy AI Search and OpenAI into a VNet using private endpoints. Restrict storage account access to the VNet.
* **Key Vault Integration**: Store any required API keys or connection strings in Azure Key Vault rather than in playbook variables.

### Troubleshooting

* **Quota errors on OpenAI deployments**: Check your subscription's Cognitive Services quota for the target region. Request increases via the Azure portal.
* **AI Search provisioning slow**: The `basic` tier can take 5-10 minutes to provision. The playbook will wait for completion.
* **Indexer failures**: After deployment, check the indexer status in the Azure portal. Common issues include missing documents in the blob container or incorrect storage connection strings.
* **Model not available in region**: Not all OpenAI models are available in all regions. Check Azure OpenAI model availability for your target region.
