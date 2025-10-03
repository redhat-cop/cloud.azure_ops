azure_configure_archost
==================

A role to Configure an Azure ARC Machine.  Once the agent is installed and run
it will register the host in the **azure_configure_archost_resource_group** requested.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_configure_archost_resource_group**: The resource group that the host will be registered in.
* **azure_configure_archost_cloud**: The Azure cloud to use. Default `AzureCloud`
* **azure_configure_archost_location**: The location to use. Default `The location of the resource_group`
* **azure_configure_archost_tenant_id**: Azure tenant id.
* **azure_configure_archost_subscription_id**: Azure subscription id.
* **azure_configure_archost_tags**: Dictionary of tags to apply to the Arc Host entry in Azure. Default: `{archost: "true"}`
* **proxy**: Object used to provide details for proxy setup if needed.  Contains the following:
  - * **hostname**: The hostname of the proxy server.
  - * **port**: The port that the proxy server is listening on.

Limitations
------------

- NA

Dependencies
------------

- NA

Example Playbook
----------------

    - name: Deploy arc agent on arc_hosts
      hosts: arc_hosts
      tasks:
        - name: Configure Arc Hosts
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_configure_archost

Example Inventory
-----------------

    [arc_hosts]
    arc-host-01 ansible_user=admin
    arc-host-02 ansible_user=admin
    arc-host-03 ansible_user=admin
    WIN-3B6PDJQPRS4 ansible_user=vagrant ansible_shell_type=powershell

    [all:vars]
    ansible_ssh_extra_args='-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
    azure_configure_archost_resource_group=YOURRESOURCEGROUP
    azure_configure_archost_subscription_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    azure_configure_archost_tenant_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
