azure_manage_snapshot
==================

A role to Create/Delete/Restore an Azure OS Disk Snapshot.

Requirements
------------

* Azure User Account with valid permission

Role Variables
--------------

* **azure_manage_snapshot_operation**: Operation to perform. Valid values are 'create', 'delete', 'restore'. Default is 'create'.
* **azure_manage_snapshot_resource_group**: (Required) Resource group on/from which the snapshot will reside.
* **azure_manage_snapshot_location**: The location to use, if not specified it will use the location of the virtual machine.
* **azure_manage_snapshot_name**: (Required) The name of the snapshot volume.
* **azure_manage_snapshot_vm_name**: The name of the virtual machine where the snapshot came from or will be applied.
* **azure_manage_snapshot_disk_name**: The name of the disk that the snapshot will be restored to.

Limitations
------------

- NA

Dependencies
------------

- NA

Example Playbook
----------------

    - hosts: localhost
      tasks:
        - name: Create a snapshot from a virtual machine
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_snapshot
          vars:
            azure_manage_snapshot_operation: create
            azure_manage_snapshot_resource_group: 'resource-group'
            azure_manage_snapshot_vm_name: 'example-vm'
            azure_manage_snapshot_name: 'example-snapshot-volume'
            azure_manage_disk_name: 'example-disk-volume'

        - name: Restore a snapshot to a virtual machine
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_snapshot
          vars:
            azure_manage_snapshot_operation: restore
            azure_manage_snapshot_resource_group: 'resource-group'
            azure_manage_snapshot_vm_name: 'example-vm'
            azure_manage_snapshot_name: 'example-snapshot-volume'
            azure_manage_disk_name: 'example-disk-volume'

        - name: Delete a snapshot
          ansible.builtin.include_role:
            name: cloud.azure_ops.azure_manage_snapshot
          vars:
            azure_manage_snapshot_operation: delete
            azure_manage_snapshot_resource_group: 'resource-group'
            azure_manage_snapshot_name: 'example-snapshot-volume'

License
-------

GNU General Public License v3.0 or later

See [LICENCE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

Author Information
------------------

- Ansible Cloud Content Team
