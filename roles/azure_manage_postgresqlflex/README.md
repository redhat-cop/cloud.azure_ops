azure_manage_postgresqlflex
==================

A role to Create/Delete/Configure an Azure Database for PostgreSQL server.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_postgresqlflex_operation**: Operation to perform. Valid values are 'create', 'delete'. Default is **create**
* **azure_manage_postgresqlflex_delete_server**: Relevant for **delete** operation. Change to true in case PostgreSQL Server deletion should be done as part of this role deletion (default: false)
* **azure_manage_postgresqlflex_resource_group**: Resource group on/from which the Database server will be created/deleted. When **operation** is set to create, this resource group will be created if not existing.
* **azure_manage_postgresqlflex_region**: An Azure location for the resources.
* **azure_manage_postgresqlflex_tags**: Dictionary of string:string pairs to assign as metadata to the object.
* **azure_manage_postgresqlflex_name**: The name of the Server.
* **azure_manage_postgresqlflex_sku**: The SKU (pricing tier) of the server.
  - **name**: The name of the SKU, typically, tier + family + cores, for example **B_Gen4_1**, **GP_Gen5_8**.
  - **tier**: The tier of the particular SKU. Valid values are Burstable, GeneralPurpose, MemoryOptimized.
* **azure_manage_postgresqlflex_storage**: Storage properties of a server.
  - **storage_size_gb**: The storage size for the server
* **azure_manage_postgresqlflex_backup**: Object used to provide details for backup. Contains the following:
  - **geo_redundant_backup**: A value indicating whether Geo-Redundat backup is enabled on the server. Default: **False**
  - **backup_retention_days**: Backup retention period between 7 and 35 days. 7 days by default if not set
* **azure_manage_postgresqlflex_version**: Server version. Valid values are '11', '12', '13', '14', '15', '16', '17'. Default: '**11**'
* **azure_manage_postgresqlflex_admin_username**: The administrator's login name of a server. Can only be specified when the server is being created (and is required for creation).
* **azure_manage_postgresqlflex_admin_password**: The password of the administrator login.
The supplied password must be between 6-72 characters long and must satisfy at least 3 of password complexity requirements from the following:
	-  Contains an uppercase character
	-  Contains a lowercase character
	-  Contains a numeric digit
	-  Contains a special character
	-  Control characters are not allowed
* **azure_manage_postgresqlflex_create_mode**: Create mode of SQL Server. Blank (Default), or restore from point in time (PointInTimeRestore). Valid values are: **Default**, **Create**, **Update**, **PointInTimeRestore**. Default value is 'Default'.
* **azure_manage_postgresqlflex_source_server_id**: Id of the source server if **azure_manage_postgresqlflex_create_mode** is set to **default**.
* **azure_manage_postgresqlflex_restore_point_in_time**: Restore point creation time (ISO8601 format), specifying the time to restore from. Required if **azure_manage_postgresqlflex_create_mode** is set to **PointInTimeRestore**.
* **azure_manage_postgresqlflex_firewall_rules**: list of firewall rule to add/remove to the PostgreSQL Server. Each items consists of:
  - **name**: The name of the PostgreSQL firewall rule.
  - **start_ip_address**: The start IP address of the PostgreSQL firewall rule. Must be IPv4 format.
  - **end_ip_address**: The end IP address of the PostgreSQL firewall rule. Must be IPv4 format.
* **azure_manage_postgresqlflex_database_instances**: list of database instances to create/delete on/from the PostgreSQL Server. Each items consists of:
  - **name**: The name of the PostgreSQL database instance.
  - **charset**: The charset of the database. Check [PostgreSQL documentation](https://www.postgresql.org/docs/9.3/multibyte.html) for possible values. This is only set on creation, use **force** to recreate a database if the values don't match.
  - **collation**: The collation of the database. Check [PostgreSQL documentation](https://www.postgresql.org/docs/9.1/collation.html). This is only set on creation, use **force** to recreate a database if the values don't match.
  - **force**:  When set to **True**, will delete and recreate the existing PostgreSQL database if any of the properties don't match what is set. Ignore when **operation** is set to **delete**.
* **azure_manage_postgresqlflex_delete_resource_group**: Relevant for **delete** operation. Change to true in case Resource Group deletion should be done as part of this role deletion (default: false)


Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      tasks:
        - name: Create PostgreSQL server
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_postgresqlflex
          vars:
            azure_manage_postgresqlflex_postgresql_name: postgresql-server
            azure_manage_postgresqlflex_operation: create
            azure_manage_postgresqlflex_region: 'eastus'
            azure_manage_postgresqlflex_resource_group: 'resource-group'
            azure_manage_postgresqlflex_postgresql_backup
              backup_retention_days: 10
            azure_manage_postgresqlflex_postgresql_admin_username: 'azureuser'
            azure_manage_postgresqlflex_postgresql_admin_password: 'Password123!'
            azure_manage_postgresqlflex_postgresql_storage:
              storage_size_gb: 128
            azure_manage_postgresqlflex_postgresql_sku:
              name: B_Gen5_1
              tier: Burstable
            azure_manage_postgresqlflex_tags:
              tag0: "tag0"
              tag1: "tag1"
            azure_manage_postgresqlflex_postgresql_firewall_rule:
              - name: rule_0
                start_ip_address: 172.10.1.0
                end_ip_address: 172.10.128.0

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
