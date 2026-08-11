azure_manage_ai_search
==============

A role to manage Azure AI Search (formerly Cognitive Search) services. User can create or delete search services.

Requirements
------------

* Azure User Account with valid permission
* `azure.azcollection` >= 3.9.0

Role Variables
--------------

* **azure_manage_ai_search_operation** - Operation to perform. Valid values are 'create', 'delete'. Default: **create**
* **azure_manage_ai_search_name** - The name of the search service. Must be 2-60 characters, lowercase letters, digits, and dashes only, globally unique.
* **azure_manage_ai_search_resource_group** - Resource group on/from which the search service will be created/deleted.
* **azure_manage_ai_search_region** - An Azure location for the search service.
* **azure_manage_ai_search_sku** - The pricing tier of the search service. Valid values are 'free', 'basic', 'standard', 'standard2', 'standard3', 'storage_optimized_l1', 'storage_optimized_l2'. Default: **basic**
* **azure_manage_ai_search_replica_count** - The number of replicas in the search service (1-12 for standard, 1-3 for basic). Default: **1**
* **azure_manage_ai_search_partition_count** - The number of partitions in the search service (1, 2, 3, 4, 6, or 12). Default: **1**
* **azure_manage_ai_search_identity** - The managed identity type. Valid values are 'None', 'SystemAssigned'. Default: **SystemAssigned**
* **azure_manage_ai_search_public_network_access** - Whether the search service is accessible from the public internet. Default: **enabled**
* **azure_manage_ai_search_tags** - Dictionary of string:string pairs to assign as metadata to the object.

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      tasks:
        - name: Create AI Search service
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_ai_search
          vars:
            azure_manage_ai_search_operation: create
            azure_manage_ai_search_region: 'eastus'
            azure_manage_ai_search_name: 'my-search-service'
            azure_manage_ai_search_resource_group: 'resource-group'
            azure_manage_ai_search_sku: 'basic'
            azure_manage_ai_search_tags:
              tag0: "tag0"
              tag1: "tag1"

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
