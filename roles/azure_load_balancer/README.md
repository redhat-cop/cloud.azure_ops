azure_load_balancer
==================

A role to Create/Delete/Configure an Azure Load Balancer.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **operation**: Operation to perform. Valid values are 'create', 'delete'. Default is **create**.
* **azure_resource_group**: Resource group on/from which the load balancer will reside. When **operation** is set to create, this resource group will be created if it does not exist.
* **azure_region**: An Azure location for the resources.
* **azure_tags**: Dictionary of string:string pairs to assign as metadata to the resource group.
* **azure_load_balancer**: Object used to provide details for a load balancer. Contains the following:
  - **name**: (Required) Name of the load balancer.
  - **public_ip_name**: Name of load balancer's public ip. Will be defaulted to '**name**-ip' if omitted.
  - **frontend_ip_configurations**: List of frontend IPs to be used. If omitted a default will be created with the name of 'default' using the load balancers public ip. Each frontend IP consists of:
    - **name**: Name of the frontend ip configuration.
    - **public_ip_address**: Name of existing public IP address object in the current resource group to be associated with.
  - **backend_address_pools**: List of backend address pools where network interfaces can be attached. If omitted a default will be created with name 'default'. Each backend address pool consists:
    - **name**: Name of the backend address pool.
  - **probes**: List of probe definitions used to check endpoint health. Each probe definition consists of:
    - **name**: Name of the probe.
    - **port**: Probe port for communicating the probe. Possible values range from 1 to 65535, inclusive.
    - **fail_count**: The number of probes which, if there is no response, will result in stopping further traffic from being delivered to the endpoint. This value allows endpoints to be taken out of rotation faster or slower than the typical times used in Azure. Default value is '3'.
    - **interval**: Interval (in seconds) for how frequently to probe the endpoint for health status. Default value is '15' and the minimum value is '5'.
    - **protocol**: Protocol of the endpoint to be probed. If 'Tcp' is specified, a received ACK is required for the probe to be successful. If 'Http' or 'Https' is specified, a 200 OK response from the specified URL is required for the probe to be successful.
    - **request_path**: The URI used for requesting health status from the VM. Path is required if protocol=Http or protocol=Https. Otherwise, it is not allowed.
  - **rules**: List of load balancing rules. Each rule consists of:
    - **name**: Name of the load balancing rule.
    - **probe**: Name of the load balancer probe this rule should use.
    - **backend_address_pool**: Name of backend address pool, where inbound traffic is randomly load balanced across the IPs in the pool.
    - **frontend_ip_configuration**: Name of frontend ip configuration to apply rule to.
    - **backend_port**: The port used for internal connections on the endpoint. Acceptable values are between 0 and 65535. Note that value 0 enables "Any Port".
    - **enable_floating_ip**: Configures a virtual machine's endpoint mapping to the Frontend IP address of the Load Balancer instead of backend instance's IP.
    - **frontend_port**: The port for the external endpoint. Frontend port numbers must be unique across all rules within the load balancer. Acceptable values are between 0 and 65534. Note that value 0 enables "Any Port".
    - **idle_timeout**: The timeout for the TCP idle connection. The value can be set between 4 and 30 minutes. The default value is 4 minutes. This element is only used when the protocol is set to TCP.
    - **load_distribution**: Session persistence policy for this rule. Valid choices are 'Default' (no persistence), 'SourceIP', 'SourceIPProtocol'.
    - **protocol**: IP protocol for the rule. Valid choices are: 'Tcp', 'Udp', 'All'.
  - **sku**: Load balancer SKU. Valid choices are: 'Basic', 'Standard'. Will also be applied to the public ip generated for the load balancer.
  - **tags**: Dictionary of string:string pairs to assign as metadata to the load balancer.

Limitations
------------

- Every load balancer will be assigned a public ip - which will be deleted when the load balancer is deleted.
- Only one backend pool is supported.
- Cannot 'remove' any ip configurations, backend pools, probes, or rules from a load balancer. Instead, `tasks/create.yml` needs to be used to update the load balancer with the desired state.

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
        - role: cloud.azure_roles.azure_load_balancer
          operation: "create"
          azure_region: "canadacentral"
          azure_resource_group: "rg"
          azure_load_balancer:
            name: "{{ azure_resource_group }}-lb"
            probes:
              - name: lb-probe
                port: 5000
            rules:
              - name: lb-rule
                probe: lb-probe
                backend_address_pool: 'default'
                frontend_ip_configuration: 'default'
                frontend_port: 5000
                backend_port: 5000
            sku: 'Standard'
            tags:
              tag0: 'test0'
              tag1: 'test1'

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/ansible-collections/cloud.azure_roles/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team