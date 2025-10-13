# Deploying ARC Hosts

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
