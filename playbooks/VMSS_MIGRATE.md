## cloud.azure_ops.vmss_migrate playbook

A playbook to migrate virtual machines of a web application from one Azure region to another region.

Variables
--------------

###### Common
--------------

* **source_resource_group**: The origin resource group. Should not be equal to **destination_resource_group**. Default: `src_rg`
* **source_region**: The origin Azure region. Default: `eastus`
* **destination_resource_group**: The destination resource group. Should not be equal to **source_resource_group**. Default: `dst_rg`
* **destination_region**: The destination Azure region. Default: `canadacentral`


--------------
###### Networking
--------------

* **azure_vnet_address_prefixes_cidr**: The virtual network CIDR address prefixes. Default: `['10.1.0.0/16']`
* **azure_subnet_address_prefixes_cidr**: The subnet CIDR address prefixes. Default: `10.1.0.0/24`

--------------
###### Virtual machines
--------------
* **azure_vm_name**: Virtual machine scaleset name prefix, the name of the scaleset will be `{{ azure_vm_name }}ss`. Default: `webapp-vm-`
* **azure_vm_user**: Virtual machine user. Default: `ansible`
* **azure_vm_user_password**: Virtual machine user password. Default: `4fB5In3ueO7,`

--------------
###### PostgreSQL
--------------
* **azure_postgresql_name**: The name of the PostgreSQL server. Default: `{{ azure_resource_group | replace('_', '-') }}-dbserver`
* **azure_postgresql_admin_username**: The database server admin user. Default: `ansible`
* **azure_postgresql_admin_password**: The database server admin user password. Default: `4fB5In3ueO7,`
* **azure_postgresql_database_instances**: The list of database instances. Default: `[{'name': 'pyapp', 'charset': 'UTF8'}]`
* **azure_postgresql_firewall_rules**: The database firewall rules. Default: `[{'name': 'allow_all', 'start_ip_address': '0.0.0.0', 'end_ip_address': '255.255.255.255'}]`

--------------
###### Web application
--------------

* **py_application**: Object used to provide details for the web application. Contains the following:
  - * **env**: The python flask application environment. Default: `development`
  - * **admin_user**: The web application admin user. Default: `admin`
  - * **admin_password**: The web application admin user password: Default: `admin`
  - * **docker_image**: The name of the Docker image to build. Default: `pywebapp`
  - * **docker_dir**: Path on virtual machine where Docker files will be downloaded. Default: `/app/pyapp`
  - * **container_name**: The name of the container to start on the VM. Default: `myapp-container`

* **application_force_init**: Whether to force application initialization, this will delete existing data from the databse. Default: `false`
* **application_src**: Remote repository application source code. Default: `https://github.com/abikouo/webapp_pyflask_demo.git`
* **playbook_number_forks**: number of parallel fork to use to deploy application into VM. Default: `15`
