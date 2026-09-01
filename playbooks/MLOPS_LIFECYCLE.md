## cloud.azure_ops.mlops_lifecycle playbook

A playbook to automate the full MLOps lifecycle on Azure using Azure Machine Learning, from workspace provisioning through model deployment and monitoring.

This reference architecture demonstrates how Ansible Automation Platform (AAP) orchestrates the complete ML lifecycle: workspace provisioning, compute management, data preparation, model training, registry-based cross-workspace sharing, and blue/green model deployment with automated rollback.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AAP Workflow (Orchestrator)                       │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Provision    │───▶│  Train       │───▶│  Deploy               │  │
│  │  (Phase 1-3)  │    │  (Phase 4-8) │    │  (Phase 9-10)        │  │
│  └──────────────┘    └──────────────┘    └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌───────────────────────┐
│  Dev Workspace   │  │  ML Registry    │  │  Prod Workspace       │
│                  │  │  (Cross-WS)     │  │                       │
│  ┌────────────┐  │  │  ┌───────────┐  │  │  ┌─────────────────┐  │
│  │ Compute    │  │  │  │ Model v1  │  │  │  │ Online Endpoint  │  │
│  │ Cluster    │  │  │  │ Model v2  │  │  │  │                  │  │
│  └────────────┘  │  │  └───────────┘  │  │  │ ┌─────┐ ┌─────┐ │  │
│  ┌────────────┐  │  │                 │  │  │ │Blue │ │Green│ │  │
│  │ Datastore  │  │  │                 │  │  │ │ 0%  │ │100% │ │  │
│  │ Data Asset │  │  │                 │  │  │ └─────┘ └─────┘ │  │
│  └────────────┘  │  │                 │  │  └─────────────────┘  │
│  ┌────────────┐  │  │                 │  │                       │
│  │ Environ.   │  │  │                 │  │                       │
│  │ Component  │  │  │                 │  │                       │
│  └────────────┘  │  │                 │  │                       │
│  ┌────────────┐  │  │                 │  │                       │
│  │ Training   │──┼──┼──▶ Register ───┼──┼──▶ Deploy from       │
│  │ Job        │  │  │                 │  │    registry           │
│  └────────────┘  │  │                 │  │                       │
└─────────────────┘  └─────────────────┘  └───────────────────────┘
```

#### Lifecycle Stages

| Phase | Stage | Description | AAP Orchestration Point |
|-------|-------|-------------|------------------------|
| 1 | Workspace Dependencies | Storage, Key Vault, App Insights, ACR | Provision shared infrastructure |
| 2 | ML Workspaces | Dev + Prod workspaces | Configure workspace-level settings |
| 3 | ML Registry | Cross-workspace model sharing | Enable environment promotion |
| 4 | Compute | Training compute clusters | Scale compute for workload |
| 5 | Data | Datastores and data assets | Register and version datasets |
| 6 | Environment | Container images for training | Pin reproducible environments |
| 7 | Component | Reusable pipeline components | Share training logic across teams |
| 8 | Training Job | Submit and monitor model training | Trigger on data/code changes |
| 9 | Model | Register and promote models | Gate promotion with validation |
| 10 | Endpoint | Blue/green deployment with traffic splitting | Automate safe rollouts |

### Blue/Green Deployment Pattern

The playbook implements a progressive traffic-shifting strategy with automated rollback:

```
Step 1: Blue (v1) = 100%                    [Initial state]
Step 2: Deploy Green (v2) with 0% traffic   [Provision new version]
Step 3: Validate Green deployment health    [Automated check]
        ├── If FAILED → Keep Blue at 100%   [Automatic rollback]
        └── If SUCCEEDED → Continue ─┐
Step 4: Blue = 90%, Green = 10%      │      [Canary]
Step 5: Blue = 50%, Green = 50%      │      [Split]
Step 6: Blue = 0%, Green = 100%      │      [Promote]
Step 7: Delete Blue deployment       │      [Cleanup]
```

Traffic percentages are configurable via variables:

```yaml
azure_ml_traffic_canary:
  blue: 90
  green: 10
azure_ml_traffic_split:
  blue: 50
  green: 50
azure_ml_traffic_final:
  blue: 0
  green: 100
```

### Cross-Workspace Model Sharing

The playbook demonstrates the ML Registry pattern for promoting models across environments:

1. **Train** in the dev workspace using dev compute and data
2. **Register** the model in the dev workspace from job output
3. **Share** by registering the model in an ML Registry (accessible from any workspace)
4. **Deploy** the model from the registry into the prod workspace online endpoint

This decouples training infrastructure from serving infrastructure while maintaining model lineage.

### CI/CD Integration with AAP Workflows

This playbook can be integrated into an AAP workflow template for automated CI/CD:

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│ Code/Data   │────▶│ AAP Workflow  │────▶│ Notification   │
│ Change      │     │              │     │                │
│ (Webhook)   │     │ 1. Train     │     │ - Slack        │
│             │     │ 2. Validate  │     │ - Email        │
└─────────────┘     │ 3. Register  │     │ - ServiceNow   │
                    │ 4. Deploy    │     └────────────────┘
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Approval     │
                    │ Gate         │
                    │ (Optional)   │
                    └──────────────┘
```

**AAP Workflow Configuration:**

1. **Trigger**: Configure a webhook in AAP that fires when new training data is pushed or code is merged
2. **Training Job Template**: Run the playbook with `operation=create` targeting the training phases
3. **Approval Node**: Optional manual approval gate before production deployment
4. **Deployment Job Template**: Run the blue/green deployment phases against the prod workspace
5. **Notification**: Send deployment status via AAP notification templates

### Prerequisites

* Azure subscription with sufficient quota for ML compute
* `azure.azcollection` >= 3.19.0 installed (for ML registry support)
* Azure credentials configured (service principal, managed identity, or CLI auth)
* The following Azure resource providers must be registered on the subscription:
  - `Microsoft.MachineLearningServices`
  - `Microsoft.Storage`
  - `Microsoft.KeyVault`
  - `Microsoft.ContainerRegistry`
  - `Microsoft.Insights`

Variables
--------------

###### Common
--------------

* **azure_resource_group**: (Required) Resource group for all MLOps resources.
* **azure_region**: An Azure location for the resources. Default: `eastus`
* **operation**: Operation to perform. Valid values are `create`, `delete`. Default: `create`

--------------
###### Workspace Dependencies
--------------

* **azure_storage_account_name_dev**: Dev storage account name (max 24 chars, alphanumeric only). Default: derived from `azure_resource_group` with `devml` suffix, truncated to 24 chars
* **azure_storage_account_name_prod**: Prod storage account name (max 24 chars, alphanumeric only). Default: derived from `azure_resource_group` with `prodml` suffix, truncated to 24 chars
* **azure_keyvault_name**: Key Vault name (max 24 chars). Default: derived from `azure_resource_group` with `-mlkv` suffix, truncated to 24 chars
* **azure_app_insights_name**: Application Insights name. Default: `{{ azure_resource_group }}-mlinsights`
* **azure_container_registry_name**: Container Registry name. Default: `{{ azure_resource_group | regex_replace('[^a-z0-9]', '') }}mlacr`
* **azure_storage_container_name**: Blob container for training data. Default: `training-data`

--------------
###### ML Workspaces
--------------

* **azure_ml_workspace_name_dev**: Dev workspace name. Default: `{{ azure_resource_group }}-ml-dev`
* **azure_ml_workspace_name_prod**: Prod workspace name. Default: `{{ azure_resource_group }}-ml-prod`

--------------
###### ML Registry
--------------

* **azure_ml_registry_name**: ML registry name for cross-workspace sharing. Default: `{{ azure_resource_group }}-mlregistry`

--------------
###### Compute
--------------

* **azure_ml_compute_name**: Compute cluster name. Default: `training-cluster`
* **azure_ml_compute_vm_size**: VM size for compute nodes. Default: `Standard_DS3_v2`
* **azure_ml_compute_min_nodes**: Minimum node count (0 enables scale-to-zero). Default: `0`
* **azure_ml_compute_max_nodes**: Maximum node count. Default: `4`

--------------
###### Data
--------------

* **azure_ml_datastore_name**: Blob datastore name. Default: `training_datastore`
* **azure_ml_data_asset_name**: Data asset name. Default: `training-dataset`
* **azure_ml_data_asset_version**: Data asset version. Default: `1`

--------------
###### Environment
--------------

* **azure_ml_environment_name**: Training environment name. Default: `training-env`
* **azure_ml_environment_version**: Environment version. Default: `1`
* **azure_ml_environment_image**: Docker image for training. Default: `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest`

--------------
###### Component
--------------

* **azure_ml_component_name**: Training component name. Default: `train-component`
* **azure_ml_component_version**: Component version. Default: `1`

--------------
###### Training Job
--------------

* **azure_ml_job_name**: Training job name. Default: `mlops-training-run`
* **azure_ml_experiment_name**: Experiment name for job grouping. Default: `mlops-lifecycle`
* **azure_ml_training_command**: Training command to execute. Default: `python train.py --input_data ${{inputs.training_data}} --output_model ${{outputs.model_output}} --epochs 10`

--------------
###### Model
--------------

* **azure_ml_model_name**: Model name. Default: `mlops-model`
* **azure_ml_model_version_blue**: Model version for blue deployment. Default: `1`
* **azure_ml_model_version_green**: Model version for green deployment. Default: `2`

--------------
###### Endpoint and Deployments
--------------

* **azure_ml_endpoint_name**: Online endpoint name. Default: `{{ azure_resource_group }}-serving`
* **azure_ml_blue_deployment_name**: Blue deployment name. Default: `blue`
* **azure_ml_green_deployment_name**: Green deployment name. Default: `green`
* **azure_ml_deployment_instance_type**: VM size for serving. Default: `Standard_DS3_v2`
* **azure_ml_deployment_instance_count**: Instance count per deployment. Default: `1`

--------------
###### Traffic Configuration
--------------

* **azure_ml_traffic_initial**: Initial traffic allocation. Default: `{blue: 100, green: 0}`
* **azure_ml_traffic_canary**: Canary traffic split. Default: `{blue: 90, green: 10}`
* **azure_ml_traffic_split**: Even traffic split. Default: `{blue: 50, green: 50}`
* **azure_ml_traffic_final**: Final traffic allocation. Default: `{blue: 0, green: 100}`

### Usage

#### Create Full MLOps Lifecycle

```bash
ansible-playbook cloud.azure_ops.mlops_lifecycle \
  -e azure_resource_group=my-mlops-rg \
  -e azure_region=eastus
```

#### Delete All MLOps Resources

```bash
ansible-playbook cloud.azure_ops.mlops_lifecycle \
  -e azure_resource_group=my-mlops-rg \
  -e operation=delete
```

#### Customize Compute and Deployment

```bash
ansible-playbook cloud.azure_ops.mlops_lifecycle \
  -e azure_resource_group=my-mlops-rg \
  -e azure_ml_compute_vm_size=Standard_NC6s_v3 \
  -e azure_ml_compute_max_nodes=8 \
  -e azure_ml_deployment_instance_type=Standard_DS4_v2
```

### Security Best Practices

The playbook deploys with system-assigned managed identity and RBAC-enabled Key Vault for demo simplicity. For production deployments, consider:

* **RBAC Role Assignments**: Assign `AzureML Data Scientist` to ML workspace users. Assign `AcrPull` to workspace managed identity on the Container Registry. Use `Storage Blob Data Contributor` instead of storage account keys for datastore access.
* **Private Endpoints**: Replace public network access with private endpoints for all workspace dependencies. Set `public_network_access: Disabled` on both workspaces.
* **Network Isolation**: Deploy workspaces with managed virtual network (`managed_network: allow_only_approved_outbound`). Create private endpoints for storage, Key Vault, and ACR.
* **Key Vault Integration**: Store storage account keys and other credentials in Key Vault rather than retrieving them at runtime.
* **Model Governance**: Use model stages (`Development`, `Staging`, `Production`) to gate promotion through the ML registry. Integrate approval gates in AAP workflows.

### Troubleshooting

* **Workspace provisioning fails**: Ensure all required resource providers are registered. Check that storage account, Key Vault, and ACR names are globally unique and follow naming constraints.
* **Compute cluster stuck in provisioning**: Verify VM quota availability in the target region. Check the Azure portal for quota increase requests.
* **Training job fails**: Review job logs in Azure ML Studio. Verify the training data exists in the datastore path and the environment image is accessible.
* **Deployment provisioning fails**: Check model artifact path is valid and accessible. Verify the workspace managed identity has `AcrPull` on the Container Registry.
* **Traffic shift not taking effect**: Ensure both deployments are in `Succeeded` provisioning state before modifying traffic. The playbook automatically skips traffic shifting if the green deployment fails.
* **Cross-workspace model not found**: Verify the ML registry was created and the model was registered in the registry (not just the workspace). Check that the prod workspace has network access to the registry.
