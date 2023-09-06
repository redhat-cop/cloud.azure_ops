## cloud.azure_ops.webapp_container playbook

A playbook to deploy a web application on Azure using containers.

Variables
--------------

###### Common
--------------

* **azure_resource_group**: (Required) Resource group on/from which the web application resources will reside.
* **azure_region**: An Azure location for the resources. Default: `eastus`
* **migrate_app**: Flag for migrating from VM / creating from scratch. Default: `false`

--------------
###### Networking
--------------

* **azure_virtual_network**: The name of the virtual network for VMs. Default: `{{ azure_resource_group }}-vnet`
* **azure_vnet_address_prefixes_cidr**: The virtual network CIDR address prefixes. Default: `['10.1.0.0/16']`
* **azure_subnet**: The name of the subnet inside the virtual network. Default: `{{ azure_resource_group }}-subnet`
* **azure_subnet_address_prefixes_cidr**: The subnet CIDR address prefixes. Default: `10.1.0.0/24`
* **azure_security_group**: The network security group name. Default: `{{ azure_resource_group }}-nsg`
* **azure_load_balancer**: Object used to provide details for a load balancer. Contains the following:
  - **name**: Name of the load balancer. Default: `{{ azure_resource_group }}-lb`
  - **public_ip_name**: Name of load balancer's public ip. Default: `{{ azure_resource_group }}-lb-public-ip`
  - **backend_address_pool**: Name of backend address pools where network interfaces can be attached. Default: `{{ azure_resource_group }}-vm-pool`

--------------
###### Container
--------------
* **azure_app_force_update**: Whether to force update of existing instance when creating container instance. Default: `false`
* **azure_vm_os**: Container instance OS type. Default: `Linux`

--------------
###### PostgreSQL
--------------
* **azure_postgresql_name**: The name of the PostgreSQL server. Default: `{{ azure_resource_group | regex_replace('[^a-zA-Z0-9]', '-') }}-dbserver`
* **azure_postgresql_admin_username**: The database server admin user. Default: `ansible`
* **azure_postgresql_admin_password**: The database server admin user password. Default: `4fB5In3ueO7,`
* **azure_postgresql_database_instances**: The list of database instances. Default: `[{'name': 'pyapp', 'charset': 'UTF8'}]`

--------------
###### Web application
--------------

* **azure_app_image**: Application Docker image. Default: `quay.io/jtorcass/pywebapp`
* **azure_app_container_name**: Application container name: Default: `{{ azure_resource_group | regex_replace('[^a-zA-Z0-9]', '-') }}-container`
* **azure_app_mem**: Application memory. Default: `1`
* **azure_app_ports**: Application ports: Default: `[5000]`
* **azure_app_env_vars**: Application environment variables.
  Default:
  ```yaml
  - name: FLASK_APP
    value: /app/pyapp
  - name: FLASK_ENV
    value: development
  - name: DATABASE_HOST
    value: "{{ azure_postgresql_name }}"
  - name: DATABASE_INSTANCE
    value: "{{ azure_postgresql_database_instances[0].name }}"
  - name: DATABASE_USER
    value: "{{ azure_postgresql_admin_username }}"
  - name: DATABASE_PASSWORD
    value: "{{ azure_postgresql_admin_password }}"
  - name: ADMIN_USER
    value: admin
  - name: ADMIN_PASSWORD
    value: admin
  ```