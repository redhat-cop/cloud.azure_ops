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
[cloud.azure_ops.azure_load_balancer_with_public_ip](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_load_balancer_with_public_ip/README.md)|A role to manage Azure Load Balancer.
[cloud.azure_ops.azure_manage_postgresql](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_manage_postgresql/README.md)|A role to manage Azure PostGreSQL Database.
[cloud.azure_ops.azure_manage_network_interface](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_manage_network_interface/README.md)|A role to manage Azure Network Interface.
[cloud.azure_ops.azure_manage_networking_stack](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_manage_networking_stack/README.md)|A role to manage Azure Networking Stack.
[cloud.azure_ops.azure_manage_resource_group](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_manage_resource_group/README.md)|A role to manage Azure Resource Group.
[cloud.azure_ops.azure_manage_security_group](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_manage_security_group/README.md)|A role to manage Azure Security Group.
[cloud.azure_ops.azure_virtual_machine_with_public_ip](https://github.com/redhat-cop/cloud.azure_ops/blob/main/roles/azure_virtual_machine_with_public_ip/README.md)|A role to manage Azure Virtual Machine.


### Playbooks
Name | Description
--- | ---
cloud.azure_ops.webapp|A playbook to create a webapp on Azure.
<!--end collection content-->

## Installation and Usage

### Installation
Clone the collection repository.

```shell
  mkdir -p ~/.ansible/collections/ansible_collections/cloud/azure_roles
  cd ~/.ansible/collections/ansible_collections/cloud/azure_roles
  git clone https://github.com/redhat-cop/cloud.azure_roles
```

### Using this collection

Once installed, you can reference the cloud.azure_roles collection content by its fully qualified collection name (FQCN), for example:

```yaml
  - hosts: all
    tasks:
        - name: Create load balancer
            ansible.builtin.include_role:
                name: cloud.azure_roles.azure_load_balancer_with_public_ip
            vars:
                operation: create
                azure_resource_group: "{{ resource_group }}"
                azure_load_balancer:
                name: "{{ resource_group }}-lb"
```

### See Also

* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.


## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against this collection repository.

### Testing and Development

The project uses `ansible-lint` and `black`.
Assuming this repository is checked out in the proper structure,
e.g. `collections_root/ansible_collections/cloud/azure_roles/`, run:

```shell
  tox -e linters
```

Sanity and unit tests are run as normal:

```shell
  ansible-test sanity
```

There are also integration tests in the `molecule` directory which are meant to be run against an azure subscription.

```shell
    az login
    molecule test
```

## License

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.
