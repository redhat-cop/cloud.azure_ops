# Deploying and Configuring ARC Hosts

## cloud.azure_ops.archost_deploy playbook

A playbook to deploy Microsoft's agent on your hardware.  Once the agent is installed and run
it will register the host in the resource_group requested.

Use **arc_hosts** as the host group for all hardware that should have the arc agent installed on.

Variables
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

Inventory
--------------

The inventory you use to deploy the agent on your hardware can either be static or dynamic but you won't be using
the Azure inventory plugins since the hosts are not yet registered in Azure.  The example playbook will apply to
all hosts in the arc_hosts group.

Demo
--------------

![Alt Text](ARCHost_deploy.gif) 

## cloud.azure_ops.archost_proxy playbook

A playbook to setup the ssh proxy and relay.  Once this is executed you will be able to execute
ansible tasks on your hardware via the azure cloud.

This playbook requires the use of the dynamic inventory file.

The intent of these playbooks is to show how these roles and modules can be used.  Feel free to
copy and modify them for your specific use cases.

Variables
--------------

* **arc_host_proxy_ssh_config_file**: Location of ssh config for hosts. Default: `'/tmp/' + hostvars[item].resource_group + '-' + item + '/ssh_config'`
* **arc_host_proxy_ssh_relay_file**: Location of ssh relay config. Default: `'/tmp/' + hostvars[item].resource_group + '-' + item + '/relay_info'`
* **arc_host_proxy_ssh_private_key_file**: Location of your private ssh key to use. Default: `~/.ssh/id_rsa`
* **arc_host_proxy_ssh_proxy_folder**: Folder to store the ssh proxy command. Default: `~/.clientsshproxy`

Inventory
--------------

The azure_rm dynamic inventory plugin can be configured to return HybridCompute (ARC) hosts.  The following
example inventory config will not only generate an ansible host group called Microsoft_HybridCompute_machines
but it will also generate two additional groups, arc_linux and arc_windows.  These are a subset of
Microsoft_HybridCompute_machines and show you how you can organize your groups.

The hostvar_expressions section also configures additional variables to tell ansible how to connect to
these hosts via the ssh proxy that this playbook sets up.

Finally we show how to specify the ansible_shell_type if the system is windows.  Your windows systems
must have ssh access configured in order for this connection to work.  winrm is not supported.

Remember that this inventory config must end in azure_rm.yml in order for the inventory plugin system to
recognize it as an azure_rm inventory file.

```yaml
# Inventory plugin:
# ---
plugin: azure.azcollection.azure_rm
plain_host_names: yes
include_arc_resource_groups:
  - '*'
hostvar_expressions:
  ansible_host: "resource_group + '-' + name if 'Microsoft.HybridCompute/machines' == resource_type else (public_dns_hostnames + public_ipv4_address) | first"
  ansible_ssh_common_args: "'-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -F /tmp/' + resource_group + '-' + name + '/ssh_config' if 'Microsoft.HybridCompute/machines' == resource_type else ''"
  ansible_user: "'vagrant' if 'windows' == os_profile.system else 'admin'"
  ansible_shell_type: "'powershell' if 'windows' == os_profile.system else ''"

conditional_groups:
  arc_hosts: "'Microsoft.HybridCompute/machines' == resource_type"
  arc_linux: "'linux' == os_profile.system and 'Microsoft.HybridCompute/machines' == resource_type"
  arc_windows: "'windows' == os_profile.system and 'Microsoft.HybridCompute/machines' == resource_type"

keyed_groups:
  - prefix: ""
    key: resource_type
    separator: ""
```

Demo
--------------

![Alt Text](ARCHost_proxy.gif) 
