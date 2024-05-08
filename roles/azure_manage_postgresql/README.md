azure_manage_postgresql
==================

A role to Create/Delete/Configure an Azure Database for PostgreSQL server.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_postgresql_operation**: Operation to perform. Valid values are 'create', 'delete'. Default is **create**
* **azure_manage_postgresql_delete_option**: used with **operation** set to **delete**. This option specifies wether to delete all resources including resource group and PostgreSQL server, or only the postgresql server. If not specified only the firewall rules and/or the configuration settings and/or the database instances defined using dedicated variables will be removed from the PostgreSQL Server. Valid values are: 'all', 'server'
* **azure_manage_postgresql_resource_group**: Resource group on/from which the Database server will be created/deleted. When **operation** is set to create, this resource group will be created if not existing.
* **azure_manage_postgresql_region**: An Azure location for the resources.
* **azure_manage_postgresql_tags**: Dictionary of string:string pairs to assign as metadata to the object.
* **azure_manage_postgresql_postgresql_name**: The name of the Server.
* **azure_manage_postgresql_postgresql_sku**: The SKU (pricing tier) of the server.
  - **name**: The name of the SKU, typically, tier + family + cores, for example **B_Gen4_1**, **GP_Gen5_8**.
  - **tier**: The tier of the particular SKU. Valid values are **Basic**, **Standard**.
  - **capacity**: The scale up/out capacity, representing the server's compute units.
  - **size**: The size code, to be interpreted by resource as appropriate.
* **azure_manage_postgresql_postgresql_storage_mb**: The maximum storage allowed for a server.
* **azure_manage_postgresql_postgresql_geo_redundant_backup**: Choose between locally redundant(default) or geo-redundant backup. This cannot be updated after first deployment. Default: **False**
* **azure_manage_postgresql_postgresql_backup_retention_days**: Backup retention period between 7 and 35 days. 7 days by default if not set
* **azure_manage_postgresql_postgresql_version**: Server version. Valid values are '9.5', '9.6', '10', '11'. Default: '**9.5**'
* **azure_manage_postgresql_postgresql_enforce_ssl**: Enable SSL enforcement. Default: False
* **azure_manage_postgresql_postgresql_storage_autogrow**: Enable storage autogrow. Default: False
* **azure_manage_postgresql_postgresql_admin_username**: The administrator's login name of a server. Can only be specified when the server is being created (and is required for creation).
* **azure_manage_postgresql_postgresql_admin_password**: The password of the administrator login. When this is not defined, the role will generated a password that can be read later in the variable name.
* **azure_manage_postgresql_postgresql_create_mode**: Create mode of SQL Server. Blank (default), restore from geo redundant (geo_restore), or restore from point in time (point_in_time_restore). Valid values are: **default**, **geo_restore**, **point_in_time_restore**. Default value is 'default'.
* **azure_manage_postgresql_postgresql_source_server_id**: Id of the source server if **azure_manage_postgresql_postgresql_create_mode** is set to **default**.
* **azure_manage_postgresql_postgresql_restore_point_in_time**: Restore point creation time (ISO8601 format), specifying the time to restore from. Required if **azure_manage_postgresql_postgresql_create_mode** is set to **point_in_time_restore**.
* **azure_manage_postgresql_tags** - Dictionary of string:string pairs to assign as metadata to the object.
* **azure_manage_postgresql_postgresql_settings**: list of configuration settings for PostgreSQL Server. 
  - **name**: setting name.
  - **value**: value of the setting.
* **azure_manage_postgresql_postgresql_firewall_rules**: list of firewall rule to add/remove to the PostgreSQL Server. Each items consists of:
  - **name**: The name of the PostgreSQL firewall rule.
  - **start_ip_address**: The start IP address of the PostgreSQL firewall rule. Must be IPv4 format.
  - **end_ip_address**: The end IP address of the PostgreSQL firewall rule. Must be IPv4 format.
* **azure_manage_postgresql_postgresql_database_instances**: list of database instances to create/delete on/from the PostgreSQL Server. Each items consists of:
  - **name**: The name of the PostgreSQL database instance.
  - **charset**: The charset of the database. Check [PostgreSQL documentation](https://www.postgresql.org/docs/9.3/multibyte.html) for possible values. This is only set on creation, use **force** to recreate a database if the values don't match.
  - **collation**: The collation of the database. Check [PostgreSQL documentation](https://www.postgresql.org/docs/9.1/collation.html). This is only set on creation, use **force** to recreate a database if the values don't match.
  - **force**:  When set to **True**, will delete and recreate the existing PostgreSQL database if any of the properties don't match what is set. Ignore when **operation** is set to **delete**.


Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      roles:
         - role: cloud.azure_ops.azure_manage_postgresql
           azure_manage_postgresql_postgresql_name: postgresql-server
           azure_manage_postgresql_operation: "create"
           azure_manage_postgresql_region: "eastus"
           azure_manage_postgresql_resource_group: "postgresql-rg"
           azure_manage_postgresql_postgresql_backup_retention_days: 10
           azure_manage_postgresql_postgresql_admin_username: ansible
           azure_manage_postgresql_postgresql_admin_password: ansible-testing-123
           azure_manage_postgresql_postgresql_storage_mb: 5120
           azure_manage_postgresql_postgresql_sku:
              name: B_Gen5_1
              tier: Basic
           azure_manage_postgresql_resource_group_tags:
              tag0: "tag0"
              tag1: "tag1"
           azure_manage_postgresql_postgresql_settings:
              - name: deadlock_timeout
                value: 2000
           azure_manage_postgresql_postgresql_firewall_rule:
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
