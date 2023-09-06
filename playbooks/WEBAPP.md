## cloud.azure_ops.webapp playbook

A playbook to deploy a web application on Azure using virtual machines.

Variables
--------------

###### Common
--------------

* **azure_resource_group**: (Required) Resource group on/from which the web application resources will reside.
* **azure_region**: An Azure location for the resources. Default: `eastus`
* **azure_tags**: Dictionary of string:string pairs to assign as metadata to the resources.
  Default: `{'application': 'python-demo-webapp-for-ansible-cloud-team'}`

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
  - **domain_name**: Load balancer domain name. 

--------------
###### Virtual machines
--------------
* **azure_vm_name**: Virtual machine scaleset name prefix, the name of the scaleset will be `{{ azure_vm_name }}ss`. Default: `webapp-vm-`
* **azure_vm_user**: Virtual machine user. Default: `ansible`
* **azure_vm_user_password**: Virtual machine user password. Default: `4fB5In3ueO7,`
* **azure_vm_image**: The image used to build the VM. See [azure.azcollection.azure_rm_virtualmachine](https://github.com/ansible-collections/azure/blob/5df571fbbb4cd83ad98b143157ae947f1d15b2d9/plugins/modules/azure_rm_virtualmachine.py#L136-L141). Default: `{'offer': 'RHEL', 'publisher': 'RedHat', 'sku': '7-LVM', 'version': 'latest'}`
* **azure_vm_size**: The Azure VM size. Default: `Standard_A2`
* **azure_bastion_vm_size**: The Azure VM size for the bastion VM. Default: `Standard_A1_v2`
* **azure_number_vm**: The number of VM on the virtual machine scaleset. Default: `3`

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

* **application_force_init**: Whether to force application initialization, this will delete existing data from the database. Default: `false`
* **application_src**: Remote repository application source code. Default: `https://github.com/abikouo/webapp_pyflask_demo.git`
* **playbook_number_forks**: number of parallel fork to use to deploy application into VM. Default: `15`
