azure_manage_network_interface
==================

A role to Create/Delete/Configure an Azure Network Interface.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_network_interface_operation**: Operation to perform. Valid values are 'create', 'delete'. Default is 'create'.
* **azure_manage_network_interface_resource_group**: Operation to perform. Valid values are 'create', 'delete'. Default is 'create'.
* **azure_manage_network_interface_interface**: Object used to provide details for a network interface. Contains the following:
  - **name**: (Required) Name of the network interface.
  - **vnet_name**: Name of the existing azure virtual network where the network interface will reside. Required when `operation=create`.
  - **subnet_name**: Name of the existing azure subnet where the network interface will reside. Required when `operation=create`.
  - **security_group_name**: Name of the existing security group with which to associate the network interface. If not provided, a default security group will be created when `create_with_security_group=true`.
  - **create_with_security_group**: Whether or not a default security group should be created with the network interface. Default value is 'yes'.
  - **os_type**: Determines any rules to be added to a network interface's default security group. If `os_type=Windows`, a rule allowing RDP access will be added. If `os_type=Linux`, a rule allowing SSH access will be added.
  - **enable_accelerated_networking**: Set to 'yes' to enable accelerated networking.
  - **ip_forwarding**: Set to 'yes' to enable ip forwarding.
  - **dns_servers**: List of IP addresses representing which DNS servers the network interface should look up.
  - **ip_configurations**: List of IP configurations. Each object can contain the following:
    - **name**: (Required) Name of the IP configuration.
    - **primary**: Set to 'yes' to make IP configuration the primary one. The first IP configuration is by default set to `primary=yes`.
    - **application_security_groups**: List of application security groups in which the IP configuration is included.
    - **load_balancer_backend_address_pools**: List of existing load balancer backend address pools in which the network interface will be load balanced.
    - **private_ip_address**: Private IP address for the IP configuration.
    - **private_ip_address_version**: Valid values are 'IPv4' and 'IPv6'. Default value is 'IPv4'.
    - **private_ip_allocation_method**: Valid values are 'Dynamic' and 'Static'. Default value is 'Dynamic'.
    - **public_ip_address_name**: Name of the existing public IP address to be assigned to the network interface.
    - **public_ip_allocation_method**: Valid values are 'Dynamic' and 'Static'. Default value is 'Dynamic'.
  - **tags**: Dictionary of string:string pairs to assign as metadata to the network interface.

Limitations
------------

- NA

Dependencies
------------

- Resource group must exist and contain at least one virtual network and subnet prior to creating a network interface.

Example Playbook
----------------

    - hosts: localhost
      roles:
        - name: Create a Network Interface with Default Security Group
          role: cloud.azure_ops.azure_manage_network_interface
          azure_manage_network_interface_operation: 'create'
          azure_manage_network_interface_resource_group: 'nic-example'
          azure_manage_network_interface_interface:
            name: 'nic'
            vnet_name: 'vnet'
            subnet_name: 'subnet'
            ip_configurations:
              - name: ipconf1
                public_ip_address_name: 'pip'
                primary: True
            tags:
              tag0: 'test0'
              tag1: 'test1'

        - name: Cleanup Network Interface and Default Security Group
          role: cloud.azure_ops.azure_manage_network_interface
          azure_manage_network_interface_operation: 'delete'
          azure_manage_network_interface_resource_group: 'nic-example'
          azure_manage_network_interface_interface:
            name: 'nic'

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team