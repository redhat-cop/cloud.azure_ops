azure_manage_networking_stack
================

This role create/delete azure networking stack which include virtual network and add/delete a subnet.
It will also create the resource group on which the networking stack should be attached, if not existing.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_networking_stack_operation** - operation to perform on the networking stack. Valid values are 'create', 'delete'
* **azure_manage_networking_stack_delete_option** - When deleting created resources, this is used to specified wether to remove only the subnet, the virtual network or all. Valid values are 'subnet', 'virtual_network', 'all'. Default value is 'all'.
* **azure_manage_networking_stack_resource_group** - Resource group on which the networking stack should be attached. If not existing, it will be created.
* **azure_manage_networking_stack_virtual_network** - Name of the virtual network to create/delete.
* **azure_manage_networking_stack_subnet** - Name of the subnet to create/delete.
* **azure_manage_networking_stack_security_group** - Existing security group with which to associate the subnet.
* **azure_manage_networking_stack_region** - An Azure location for the virtual network to create.
* **azure_manage_networking_stack_vnet_address_prefixes_cidr** - List of IPv4 address ranges for virtual network where each is formatted using CIDR notation.
  Required when creating a new virtual network.
* **azure_manage_networking_stack_subnet_address_prefixes_cidr** - CIDR defining the IPv4 and IPv6 address space of the subnet. Must be valid within the context of the virtual network.
* **azure_manage_networking_stack_tags** - Dictionary of string:string pairs to assign as metadata to the object.
* **azure_manage_networking_stack_delete_resource_group**: Relevant for **delete** operation. Change to true in case Resource Group deletion should be done as part of this role deletion (default: false)

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
         - role: cloud.azure_ops.azure_manage_networking_stack
           azure_manage_networking_stack_operation: "create"
           azure_manage_networking_stack_region: "eastus"
           azure_manage_networking_stack_resource_group: "testing-resource-group"
           azure_manage_networking_stack_virtual_network: "my-vnet"
           azure_manage_networking_stack_subnet: "my-subnet-00"
           azure_manage_networking_stack_vnet_address_prefixes_cidr:
            - "10.1.0.0/16"
            - "172.100.0.0/16"
           azure_manage_networking_stack_subnet_address_prefixes_cidr:
            - "172.100.0.0/8"
           azure_manage_networking_stack_tags:
             tag0: "tag0"
             tag1: "tag1"

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
