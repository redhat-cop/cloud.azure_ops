azure_manage_security_group
==============

A role to manage an Azure Security Group. User can create or delete a security group, as well as add/remove rules from a security group.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_security_group_operation**: Operation to perform. Valid values are 'create', 'delete'. Default is 'create'.
* **azure_manage_security_group_resource_group**: (Required) Resource group on/from which the security group will reside. When `azure_manage_security_group_operation='create'`, this resource group will be created if it does not exist.
* **azure_manage_security_group_region**: Azure region, required when the provided resource group does not exist.
* **azure_manage_security_group_security_group**: (Required) Object used to provide details for a security group. Contains the following:
  - **name**: (Required) Name of the security group.
  - **rules**: List of security rules to apply to a subnet or NIC. Each rule consists of:
    - **name**: (Required) Unique name of rule.
    - **priority**: (Required) Order in which to apply the rule. Must be a unique integer between 100 and 4096 inclusive.
    - **access**: 'Allow' to allow traffic flow; 'Deny' to deny traffic flow. Default is 'Allow'.
    - **description**: Description of the rule
    - **destination_address_prefix**: The destination address prefix. CIDR or destination IP range. Asterisk '\*' can be used to match all source IPs. Default tags such as 'VirtualNetwork', 'AzureLoadBalancer' and 'Internet' can also be used. Accepts string or a list of strings. Asterisk '\*' and default tags can only be specified as single string, not as a list of strings.
    - **destination_application_security_groups**: List of the destination application security groups. It could be a list of resource ids, names in same resource group, or dicts containing resource_group and name. It is mutually exclusive with destination_address_prefix and destination_address_prefixes.
    - **destination_port_range**: Port or range of ports to which traffic is headed. Can be a string or list of strings. Default is '*'.
    - **direction**: Indicates direction of traffic flow. 'Inbound' (default) or 'Outbound'.
    - **protocol**: Accepted traffic protocol. Valid inputs are '*' (default), 'Udp', 'Tcp', 'Icmp'.
    - **source_address_prefix**: The CIDR or source IP range. Asterisk '\*' can be used to match all source IPs. Default tags such as 'VirtualNetwork', 'AzureLoadBalancer' and 'Internet' can also be used. If this is an ingress rule, specifies where network traffic originates from. Accepts string a list of strings. Asterisk '\*' and default tags can only be specified as a single string, not as a list of strings.
    - **source_port_range**: Port or range of ports from which traffic originates. Can be a string or list of strings. Default is '*'.
  - **purge_rules**: (boolean) If set to 'yes', removes any existing, non-default, rules that are not specified in `rules` above.
  - **rules_to_remove**: List of strings representing the names of security group rules to be removed from the security group.
  - **tags**: Dictionary of string:string pairs to assign as metadata to the security group.

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
        - name: Create a security group with custom rules
          role: cloud.azure_ops.azure_manage_security_group
          azure_manage_security_group_resource_group: 'my_resource_group'
          azure_manage_security_group_region: eastus
          azure_manage_security_group_operation: 'create'
          azure_manage_security_group_security_group:
            name: "{{ azure_resource_group }}-sg"
            rules:
              - name: 'allow_ssh'
                protocol: Tcp
                destination_port_range:
                  - 22
                access: Allow
                priority: 100
                direction: Inbound
              - name: 'allow_web_traffic'
                protocol: Tcp
                destination_port_range:
                  - 80
                  - 443
                access: Allow
                priority: 101
                direction: Inbound

        - name: Remove rules from security group
          role: cloud.azure_ops.azure_manage_security_group
          azure_manage_security_group_resource_group: 'my_resource_group'
          azure_manage_security_group_security_group:
            name: "{{ azure_resource_group }}-sg"
            rules_to_remove:
              - 'allow_ssh'
              - 'allow_web_traffic'

License
-------

GNU General Public License v3.0 or later

See [LICENCE](../../LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
