load_balancer
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
* **azure_tags**: Dictionary of string:string pairs to assign as metadata to the object.
* **azure_lb_name**: Name of the load balancer.
* **azure_lb_pip_name**: Name of load balancer's public ip. Will be defaulted to '**azure_lb_name**-ip' if omitted.
* **azure_lb_probes**: List of probe definitions used to check endpoint health. Each probe definition consists of:
  - **name**: Name of the probe.
  - **port**: Probe port for communicating the probe. Possible values range from 1 to 65535, inclusive.
  - **fail_count**: The number of probes which, if there is no response, will result in stopping further traffic from being delivered to the endpoint. This value allows endpoints to be taken out of rotation faster or slower than the typical times used in Azure. Default value is '3'.
  - **interval**: Interval (in seconds) for how frequently to probe the endpoint for health status. Default value is '15' and the minimum value is '5'.
  - **protocol**: Protocol of the endpoint to be probed. If 'Tcp' is specified, a received ACK is required for the probe to be successful. If 'Http' or 'Https' is specified, a 200 OK response from the specified URL is required for the probe to be successful.
  - **request_path**: The URI used for requesting health status from the VM. Path is required if protocol=Http or protocol=Https. Otherwise, it is not allowed.
* **azure_lb_rules**: List of load balancing rules. Each rule consists of:
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
* **azure_lb_sku**: Load balancer SKU. Valid choices are: 'Basic', 'Standard'.
* **azure_lb_network_interface_instances**: List of NIC names to be load balanced.


Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
        - role: cloud.azure_roles.load_balancer
          operation: "create"
          azure_region: "canadacentral"
          azure_resource_group: "rg"
          azure_lb_name: testlb0
          azure_lb_network_interface_instances:
            - "{{ resource_group }}-nic1"
            - "{{ resource_group }}-nic2"
            - "{{ resource_group }}-nic3"
          azure_virtual_network: "{{ resource_group }}-vnet-00"
          azure_subnet: "{{ resource_group }}-subnet-00"
          azure_vnet_address_prefixes_cidr:
            - 10.16.0.0/16
          azure_subnet_address_prefixes_cidr: 10.16.0.0/24          

License
-------

BSD

Author Information
------------------

- Ansible Cloud Content Team