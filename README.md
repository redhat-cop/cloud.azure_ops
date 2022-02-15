# Azure Roles Collection for Ansible Automation Platform

This repository hosts the `cloud.azure_roles` Ansible Collection.

The collection includes a variety of Ansible roles and playbook to help automate the management of resources on Microsoft Azure.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.17**.

## Included content

Click on the name of a plugin or module to view that content's documentation:

<!--start collection content-->
### Roles
Name | Description
--- | ---
[cloud.azure_roles.load_balancer](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/load_balancer/README.md)|A role to manage Azure Load Balancer.
[cloud.azure_roles.managed_postgresql](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/managed_postgresql/README.md)|A role to manage Azure PostGreSQL Database.
[cloud.azure_roles.network_interface](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/network_interface/README.md)|A role to manage Azure Network Interface.
[cloud.azure_roles.networking_stack](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/networking_stack/README.md)|A role to manage Azure Networking Stack.
[cloud.azure_roles.resource_group](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/resource_group/README.md)|A role to manage Azure Resource Group.
[cloud.azure_roles.security_group](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/security_group/README.md)|A role to manage Azure Security Group.
[cloud.azure_roles.virtual_machine](https://github.com/ansible-collections/cloud.azure_roles/blob/main/roles/virtual_machine/README.md)|A role to manage Azure Virtual Machine.


### Playbooks
Name | Description
--- | ---
cloud.azure_roles.webapp|A playbook to create a webapp on Azure.
<!--end collection content-->

## Installation and Usage

### Installing the Collection from Ansible Galaxy

Before using the azure_roles collection, you need to install it with the Ansible Galaxy CLI:

    ansible-galaxy collection install cloud.azure_roles

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: cloud.azure_roles
    version: 0.1.0
```

### Testing with `molecule`

There are also integration tests in the `molecule` directory which are meant to be run against an azure subscription.

    az login
    molecule test

## License

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/ansible-collections/cloud.azure_roles/blob/main/LICENSE) to see the full text.
