azure_manage_storage_account
==============

A role to manage Azure Storage Accounts. User can create or delete storage accounts with optional blob container creation.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_storage_account_operation** - Operation to perform. Valid values are 'create', 'delete'. Default: **create**
* **azure_manage_storage_account_name** - The name of the storage account. Must be 3-24 characters, lowercase letters and numbers only.
* **azure_manage_storage_account_resource_group** - Resource group on/from which the storage account will be created/deleted.
* **azure_manage_storage_account_region** - An Azure location for the storage account.
* **azure_manage_storage_account_kind** - The kind of storage account. Default: **StorageV2**
* **azure_manage_storage_account_sku** - The storage account replication type. Default: **Standard_LRS**
* **azure_manage_storage_account_access_tier** - The access tier for BlobStorage and StorageV2 accounts. Default: **Hot**
* **azure_manage_storage_account_container_name** - Name of blob container to create. Omit to skip container creation.
* **azure_manage_storage_account_tags** - Dictionary of string:string pairs to assign as metadata to the object.

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      tasks:
        - name: Create Storage Account
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_storage_account
          vars:
            azure_manage_storage_account_operation: create
            azure_manage_storage_account_region: 'eastus'
            azure_manage_storage_account_name: 'mystorageaccount'
            azure_manage_storage_account_resource_group: 'resource-group'
            azure_manage_storage_account_container_name: 'documents'
            azure_manage_storage_account_tags:
              tag0: "tag0"
              tag1: "tag1"

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
