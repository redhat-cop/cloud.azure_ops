# Azure Roles Collection for Ansible Automation Platform

This repository hosts the `cloud.azure_ops` Ansible Collection.

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
[cloud.azure_ops.azure_load_balancer_with_public_ip_with_public_ip](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_load_balancer/README.md)|A role to manage Azure Load Balancer.
[cloud.azure_ops.azure_managed_postgresql](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_rds_postgresql/README.md)|A role to manage Azure PostGreSQL Database.
[cloud.azure_ops.azure_network_interface](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_network_interface/README.md)|A role to manage Azure Network Interface.
[cloud.azure_ops.azure_networking_stack](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_networking_stack/README.md)|A role to manage Azure Networking Stack.
[cloud.azure_ops.azure_resource_group](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_resource_group/README.md)|A role to manage Azure Resource Group.
[cloud.azure_ops.azure_security_group](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_security_group/README.md)|A role to manage Azure Security Group.
[cloud.azure_ops.azure_virtual_machine](https://github.com/ansible-collections/cloud.azure_ops/blob/main/roles/azure_virtual_machine/README.md)|A role to manage Azure Virtual Machine.


### Playbooks
Name | Description
--- | ---
cloud.azure_ops.webapp|A playbook to create a webapp on Azure.
<!--end collection content-->

## Installation and Usage

### Installing the Collection from Ansible Galaxy

Before using the cloud.azure_ops collection, you need to install it with the Ansible Galaxy CLI:

    ansible-galaxy collection install cloud.azure_ops

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: cloud.azure_ops
    version: 0.1.0
```

### Testing with `molecule`

There are also integration tests in the `molecule` directory which are meant to be run against an azure subscription.

    az login
    molecule test

## License

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/ansible-collections/cloud.azure_ops/blob/main/LICENSE) to see the full text.
