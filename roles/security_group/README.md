security_group
==============

A role to manage an Azure Security Group. User can create or delete a security group, as well as add/remove rules from a security group.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **operation** (required) - Set to 'create' to create or update a security group. Set to 'delete' to remove a security group.
* **azure_resource_group** (required) - Resource group to create or delete.
* **azure_security_group** (required) - Name of security group.
* **azure_security_group_purge_rules** - (boolean) If set to 'yes', removes any existing rules not matching the default rules. Useful for deleting rules.
* **azure_security_group_rules** - List of security rules to apply to a subnet or NIC. Each rule consists of:
  - **name** (required) - Unique name of rule.
  - **priority** (required) - Order in which to apply the rule. Must be a unique integer between 100 and 4096 inclusive.
  - **access** - 'Allow' to allow traffic flow; 'Deny" to deny traffic flow. Default is 'Allow'.
  - **description** - Description of the rule
  - **destination_address_prefix** - The destination address prefix. CIDR or destination IP range. Asterisk `*` can also be used to match all source IPs. Default tags such as `VirtualNetwork`, `AzureLoadBalancer` and `Internet` can also be used. Accepts string or a list of strings. Asterisk `*` and default tags can only be specified as single string, not as a list of strings.
  - **destination_application_security_groups** - List of the destination application security groups. It could be a list of resource ids, names in same resource group, or dicts containing resource_group and name. It is mutually exclusive with destination_address_prefix and destination_address_prefixes.
  - **destination_port_range** - Port or range of ports to which traffic is headed. Can be a string or list of strings. Default is `*`.
  - **direction** - Indicates direction of traffic flow. 'Inbound' (default) or 'Outbound'.
  - **protocol** - Accepted traffic protocol. Valid inputs are '*' (default), 'Udp', 'Tcp', 'Icmp'.
  - **source_address_prefix** - The CIDR or source IP range. Asterisk `*` can also be used to match all source IPs. Default tags such as VirtualNetwork, AzureLoadBalancer and Internet can also be used. If this is an ingress rule, specifies where network traffic originates from. Accepts string a list of strings. Asterisk `*` and default tags can only be specified as a single string, not as a list of strings.
  - **source_port_range** - Port or range of ports from which traffic originates. Can be a string or list of strings. Default is `*`.
* **azure_tags** - Dictionary of string:string pairs to assign as metadata to the object.
* **azure_security_group_rules_to_remove**: List of strings representing the names of security group rules to be removed from the security group.

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
        - role: cloud.azure_roles.security_group
          operation: "create"
          azure_region: "eastus"
          azure_resource_group: "testing-resource-group"
          azure_security_group: "testing-security-group"
          azure_security_group_rules:
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
          azure_tags:
            tag0: "tag0"
            tag1: "tag1"


License
-------

BSD

Author Information
------------------

- Ansible Cloud Content Team