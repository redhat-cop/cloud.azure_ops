==============================
Cloud.Azure\_Ops Release Notes
==============================

.. contents:: Topics

v4.0.0
======

Release Summary
---------------

This is release 4.0.0 of ``cloud.azure_ops``, released on 2024-07-09.

Bugfixes
--------

- Added 'vnet_address_prefixes_cidr' and 'subnet_address_prefixes_cidr' role variables. Required when creating a new virtual network
- Added Virtual network autocreation during Virual machine with public IP creation in case Virtual network doesn't exist for azure_virtual_machine_with_public_ip role
- Added a timeout (as a temporary solution) in the delete task of the azure_manage_resource_group role
- Added missed argument to the 'Power On VM' task in azure_virtual_machine_with_public_ip role
- Added retries to Resource Group deletion (retries=40, delay=5)
- Fix argument choices for azure_manage_postgrsql
- Fixed azure_manage_resource_group_tags value for new resource group creation by role
- Fixed undefined variables issue for azure_virtual_machine_with_public_ip role
- Refactor the management of the Resource Group by other roles Deleting the Resource Group should not be forced by default and should only occur if explicitly requested by the user.
- Removed duplicated azure_manage_postgresql_tags var in README file of azure_manage_postgresql role
- Removed the undefined variables from the create.yml of azure_manage_postgresql role and replaced them with defined ones.
- Update README.md with proper playbook examples
- Updated README with proper role's variables description for azure_virtual_machine_with_public_ip role

v3.0.0
======

Release Summary
---------------

This is release 3.0.0 of ``cloud.azure_ops``, released on 2024-04-23.

Breaking changes to role variable names which are now role_prefix based.

Minor Changes
-------------

- Add argument_specs.yaml to validate the role variables.

Breaking Changes / Porting Guide
--------------------------------

- Rename roles variables using ``role_name_`` as prefix (https://github.com/redhat-cop/cloud.azure_ops/pull/48).
- Update README.md and meta/runtime.yml to reflect our ansible core testing versions.

Bugfixes
--------

- Fix syntax in roles/azure_manage_networking_stack/README.md
- Update README.md with proper variable names in example
- Update playbooks that include credentials to be able to be used with Automation Controller (not just the command line).  https://github.com/redhat-cop/cloud.azure_ops/pull/47
- Update playbooks/roles/scale_virtual_machine/tasks/main.yml to use correct operation variable
- Update roles/azure_manage_security_group/tasks/main.yml to use correct operation variable
- Update roles/azure_virtual_machine_with_public_ip/tasks/main.yml to use correct prefix vars
- Use correct variables in roles/azure_manage_networking_stack/tasks/create.yml
- fix variable names in roles/azure_load_balancer_with_public_ip/tasks/delete.yml
- fix variable names in roles/azure_manage_security_group/tasks/delete.yml
- fix variable names in roles/azure_manage_security_group/tasks/remove_rules.yml
- playbooks/webapp_container.yml
- roles/azure_manage_resource_group - Ensure the correct variable name is used for the operation.
- roles/azure_manage_security_group: Change azure_manage_security_group_region to be optional, as it not required when the Resource Group is already exists.
- roles/azure_manage_security_group: Fix purge_rules and rules_to_remove indentation in the arguments spec
- roles/azure_virtual_machine_with_public_ip - Ensure the correct variables names are defined inside defaults.

v2.0.0
======

Breaking Changes / Porting Guide
--------------------------------

- the collection has been renamed to cloud.azure_ops (https://github.com/redhat-cop/cloud.azure_ops/pull/38).
