resource_group
==============

A role to manage Azure Resource Group. User can create or delete resource group.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* operation - Operation to perform. Valid values are 'create', 'delete'.
* resource_group_name - The name of resource group.
* resource_group_location - The name of region in which resource group needs to be placed.


Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
         - { role: cloud.azure_roles.resource_group }

License
-------

BSD

Author Information
------------------

- Ansible Cloud Content Team
