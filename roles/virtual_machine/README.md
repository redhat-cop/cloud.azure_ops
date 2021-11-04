virtual_machine
==================

A role to Create/Delete/Configure an Azure Virtual Machine.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **operation**: Operation to perform. Valid values are 'create', 'delete'. Default is **create**
* **remove_on_absent**: used with **operation** set to **delete**. This option specifies which associated resources to remove when removing a VM. Use the value 'all' to remove all resources related to the VM being removed, or 'all_autocreated' to remove the resources that were automatically created while provisioning the VM. To remove only specific resources, use the values 'network_interfaces', 'virtual_storage', or 'public_ips'. The default value is 'all'.
* **azure_resource_group**: Resource group on/from which the virtual machine will reside. When **operation** is set to create, this resource group will be created if it does not exist.
* **azure_region**: An Azure location for the resources.
* **azure_tags**: Dictionary of string:string pairs to assign as metadata to the object.
* **azure_vm_name**: Name of the virtual machine.
* **azure_vm_admin_username**: Administrator's login name of a server. Required for creation.
* **azure_vm_admin_password**: Password of the administrator login. Not required when **azure_vm_os_type** is 'Linux' and **azure_vm_ssh_pw_enabled** is 'false'.
* **azure_vm_size**: Valid Azure VM size. Choices vary depending on the subscription and location.
* **azure_network_interfaces**: Network interface names to add to the VM. Can be a string of name or resource ID of the network interface, can also be a dict containing 'resource_group' and 'name' of the network interface. A default network interface will be created if not provided.
* **azure_vm_os**: Type of Operating System. Default is 'Linux'
* **azure_availability_set_name**: Name or ID of existing availability set to add the VM to.
* **azure_vm_image**: The image used to build the VM. For custom images, the name of the image. To narrow the search to a specific resource group, a dict with the keys name and resource_group. For Marketplace images, a dict with the keys publisher, offer, sku, and version. Set version=latest to get the most recent version of a given image.
* **azure_vm_ssh_pw_enabled**: Enable/disable SSH passwords. Valid values are 'yes', 'no'. Default value is 'yes'.
* **azure_vm_ssh_public_keys**: List of SSH keys when **azure_vm_os** is 'Linux'. Accepts a list of dicts where each dictionary contains two keys, 'path' and 'key_data'. Set path to the default location of the authorized_keys files. For example, path=/home/<admin username>/.ssh/authorized_keys. Set key_data to the actual value of the public key.
* **azure_vm_data_disks**: List of data disks.
- **lun**: Logical unit number for data disk. Must be unique for each data disk attached to a VM.
- **caching**: Type of data disk caching. Options are 'ReadOnly' (default) or 'ReadWrite'.
- **disk_size_gb**: Initial disk size in GB for blank data disks. Cannot be larger than 1023 GB. Can only be modified when VM is deallocated.
- **managed_disk_type**: Managed data disk type.
- **storage_account_name**: Name of an existing storage account that supports creation of VHD blobs.
- **storage_blob_name**: Name of storage blob used to hold the OS disk image of the VM.
- **storage_container_name**: Name of the container to use within the storage account to store VHD blobs. Default is 'vhds'


Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
        - role: cloud.azure_roles.virtual_machine
          operation: "create"
          azure_region: "canadacentral"
          azure_resource_group: "vm-rg"
          azure_vm_name: testvm10
          azure_vm_admin_username: "testuser"
          azure_vm_admin_password: "Password123"
          azure_vm_image:
            offer: RHEL
            publisher: RedHat
            sku: "7-LVM"
            version: latest
          azure_vm_size: Standard_D4

License
-------

BSD

Author Information
------------------

- Ansible Cloud Content Team