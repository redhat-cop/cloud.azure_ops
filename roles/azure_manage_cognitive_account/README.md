azure_manage_cognitive_account
==============

A role to manage Azure Cognitive Services accounts (including Azure OpenAI). User can create or delete accounts.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_cognitive_account_operation** - Operation to perform. Valid values are 'create', 'delete'. Default: **create**
* **azure_manage_cognitive_account_name** - The name of the Cognitive Services account.
* **azure_manage_cognitive_account_resource_group** - Resource group on/from which the account will be created/deleted.
* **azure_manage_cognitive_account_region** - An Azure location for the account.
* **azure_manage_cognitive_account_kind** - The kind of Cognitive Services account (e.g., 'OpenAI', 'TextAnalytics', 'FormRecognizer'). Default: **OpenAI**
* **azure_manage_cognitive_account_sku** - The pricing tier name. Default: **S0**
* **azure_manage_cognitive_account_custom_subdomain** - Custom subdomain name for the account endpoint. Defaults to the account name.
* **azure_manage_cognitive_account_public_network_access** - Whether the account is accessible from the public internet. Default: **Enabled**
* **azure_manage_cognitive_account_tags** - Dictionary of string:string pairs to assign as metadata to the object.

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      tasks:
        - name: Create Azure OpenAI account
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_cognitive_account
          vars:
            azure_manage_cognitive_account_operation: create
            azure_manage_cognitive_account_region: 'eastus'
            azure_manage_cognitive_account_name: 'my-openai-account'
            azure_manage_cognitive_account_resource_group: 'resource-group'
            azure_manage_cognitive_account_kind: 'OpenAI'
            azure_manage_cognitive_account_tags:
              tag0: "tag0"
              tag1: "tag1"

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
