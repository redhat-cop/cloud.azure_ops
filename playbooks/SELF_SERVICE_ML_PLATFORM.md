## cloud.azure_ops.self_service_ml_platform playbook

A playbook to enable self-service ML workspace provisioning through Ansible Automation Platform, from shared infrastructure setup through team workspace deployment with cost controls.

This reference architecture demonstrates how AAP orchestrates multi-team ML environments: shared infrastructure provisioning (Key Vault, ACR, App Insights), isolated workspace provisioning with budget alerts, and RBAC-based access control.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AAP Self-Service Catalog                          │
│                                                                      │
│  ┌────────────────────┐         ┌──────────────────────────────┐   │
│  │ Platform Setup     │         │ Request ML Workspace         │   │
│  │ (Admin, One-time)  │         │ (Self-Service, Repeatable)   │   │
└──┼────────────────────┼─────────┼──────────────────────────────┼───┘
   │                    │         │                              │
   ▼                    ▼         ▼                              ▼
┌──────────────────┐  ┌───────────────────────────────────────────┐
│ Shared Hub       │  │  Team Workspace (Isolated)                │
│                  │  │                                           │
│ - Key Vault      │◄─┤ - ML Workspace (managed identity)        │
│ - ACR            │  │ - Storage Account (team data)            │
│ - App Insights   │  │ - Compute Cluster (scale-to-zero)        │
└──────────────────┘  │ - Budget Alerts (50%, 80%, 100%)        │
                      └───────────────────────────────────────────┘
```

### Hub-and-Spoke Model

| Component | Scope | Purpose | Cost Model |
|-----------|-------|---------|------------|
| Shared Hub | Platform-wide | Key Vault, ACR, App Insights | Shared across all teams |
| Team Spoke | Per-team | ML Workspace, Storage, Compute | Tagged per team for chargeback |

### Prerequisites

* Azure subscription with sufficient quota for ML workspaces and compute
* `azure.azcollection` >= 3.19.0 installed (for ML workspace support)
* Azure credentials configured (service principal with Contributor + User Access Administrator roles)
* The following Azure resource providers must be registered on the subscription:
  - `Microsoft.MachineLearningServices`
  - `Microsoft.Storage`
  - `Microsoft.KeyVault`
  - `Microsoft.ContainerRegistry`
  - `Microsoft.Insights`

### Variables

#### Common

* **operation**: Operation to perform. Valid values: `provision_shared_infrastructure`, `provision_team_workspace`, `delete_team_workspace`, `delete_shared_infrastructure`. Required.
* **azure_region**: Azure location for resources. Default: `eastus`
* **azure_ml_platform_environment**: Environment tag for all resources. Default: `production`
* **azure_ml_platform_cost_center**: Cost center tag for shared infrastructure. Default: `ml-platform`
* **azure_ml_platform_team**: Team tag for shared infrastructure. Default: `platform`

#### Shared Infrastructure (Hub)

* **azure_ml_platform_shared_rg**: Resource group for shared infrastructure. Default: `ml-platform-shared`
* **azure_ml_platform_keyvault**: Key Vault name (globally unique, 3-24 chars). Required for shared infrastructure provisioning.
* **azure_ml_platform_acr**: Container Registry name (globally unique, 5-50 alphanumeric chars). Required for shared infrastructure provisioning.
* **azure_ml_platform_appinsights**: Application Insights name. Default: `ml-platform-insights`
* **azure_ml_platform_admin_email**: Platform admin email for budget alerts. Required for team workspace provisioning.

#### Team Workspace (Spoke)

* **azure_ml_team_name**: Team name (lowercase, 3-20 alphanumeric/hyphens). Required for team workspace operations.
* **azure_ml_team_contact_email**: Team contact email for budget alerts. Required for team workspace provisioning.
* **azure_ml_team_budget_limit**: Monthly budget limit in USD. Default: `2500`
* **azure_ml_team_compute_vm_size**: VM size for compute cluster. Default: `Standard_DS3_v2`
* **azure_ml_team_compute_max_nodes**: Maximum nodes in compute cluster. Default: `4`
* **azure_ml_team_data_access_scope**: Data access requirements. Valid values: `restricted`, `shared`, `external`. Default: `restricted`

### Usage

#### Provision Shared Infrastructure (Platform Admin, One-Time)

```bash
ansible-playbook cloud.azure_ops.self_service_ml_platform \
  -e operation=provision_shared_infrastructure \
  -e azure_ml_platform_shared_rg=ml-platform-shared \
  -e azure_ml_platform_keyvault=ml-platform-kv-001 \
  -e azure_ml_platform_acr=mlplatformacr001 \
  -e azure_region=eastus
```

#### Provision Team Workspace (Self-Service, Repeatable)

```bash
ansible-playbook cloud.azure_ops.self_service_ml_platform \
  -e operation=provision_team_workspace \
  -e azure_ml_platform_shared_rg=ml-platform-shared \
  -e azure_ml_team_name=datascience-alpha \
  -e azure_ml_team_contact_email=ds-alpha@company.com \
  -e azure_ml_team_budget_limit=5000 \
  -e azure_ml_team_compute_vm_size=Standard_DS4_v2 \
  -e azure_ml_team_compute_max_nodes=8 \
  -e azure_ml_platform_admin_email=admin@company.com
```

#### Delete Team Workspace

```bash
ansible-playbook cloud.azure_ops.self_service_ml_platform \
  -e operation=delete_team_workspace \
  -e azure_ml_platform_shared_rg=ml-platform-shared \
  -e azure_ml_team_name=datascience-alpha
```

#### Delete Shared Infrastructure

```bash
ansible-playbook cloud.azure_ops.self_service_ml_platform \
  -e operation=delete_shared_infrastructure \
  -e azure_ml_platform_shared_rg=ml-platform-shared \
  -e azure_ml_platform_keyvault=ml-platform-kv-001 \
  -e azure_ml_platform_acr=mlplatformacr001
```

### AAP Integration

This playbook is designed to be called from AAP workflow templates via self-service surveys.

#### Survey 1: Platform Setup (Admin)

**Purpose:** One-time shared infrastructure provisioning

**Fields:**
- Azure Region (multiplechoice: eastus, westus2, westeurope)
- Resource Group Name (text, default: ml-platform-shared)
- Key Vault Name (text, globally unique)
- Container Registry Name (text, globally unique, alphanumeric only)
- Platform Admin Email (text, email validation)

**Workflow:** Calls playbook with `operation=provision_shared_infrastructure`

#### Survey 2: Request ML Workspace (Self-Service)

**Purpose:** Team workspace provisioning

**Fields:**
- Team Name (text, lowercase alphanumeric/hyphens, 3-20 chars)
- Team Contact Email (text, email validation)
- Monthly Budget Limit (multiplechoice: $1000, $2500, $5000, $10000)
- Compute VM Size (multiplechoice: DS3_v2, DS4_v2, NC6s_v3, NC12s_v3)
- Maximum Compute Nodes (multiplechoice: 2, 4, 8, 16)
- Data Access Scope (multiplechoice: restricted, shared, external)

**Workflow:**
1. Validate request (budget calculation, name uniqueness)
2. Approval gate if budget > $5000 or GPU requested
3. Provision workspace (calls playbook with `operation=provision_team_workspace`)
4. Generate RBAC instructions for platform admin
5. Notify team and admin

Survey JSON exports and workflow templates can be generated from the field specifications above.

### Cost Controls

#### Budget Alerts

- **Action Group:** Email notifications to team contact and platform admin
- **Alert Thresholds:** 50%, 80%, 100% of monthly budget
- **Scope:** Filtered by team tag on all resources

#### Auto-Shutdown

- **Compute Cluster:** Scales to zero after 5 minutes idle (`min_instances: 0`)
- **Cost Allocation:** All resources tagged with `team`, `cost_center`, `environment`, `budget_limit`, and `provisioned_date` for chargeback and cost tracking

### Security Best Practices

The playbook deploys with system-assigned managed identity and RBAC-enabled Key Vault. For production deployments, consider:

* **RBAC Role Assignments:** Manually assign `AzureML Data Scientist` role to team members on workspace. Platform admin assigns roles post-provisioning.
* **Private Endpoints:** Replace public network access with private endpoints for workspaces, storage, Key Vault, ACR.
* **Network Isolation:** Deploy workspaces with managed virtual network (`managed_network: allow_only_approved_outbound`).
* **Key Vault Secrets:** Store external API keys in Key Vault, grant workspace identity `Key Vault Secrets User` role.
* **Multi-Team Isolation:** Each team has dedicated workspace and storage account. Shared Key Vault and ACR reduce costs while maintaining security boundaries.

### Troubleshooting

* **Shared infrastructure provisioning fails:** Ensure resource providers are registered. Check Key Vault and ACR names are globally unique.
* **Team workspace provisioning fails:** Verify shared infrastructure exists in specified resource group. Check workspace name doesn't already exist.
* **Compute cluster stuck provisioning:** Verify VM quota available in region. Check Azure portal for quota increase requests.
* **Budget alerts not firing:** Verify action group email delivered. Budget API can take 24 hours to activate. Check budget scope includes team tag.
* **RBAC permissions errors:** Service principal needs Contributor + User Access Administrator roles to assign managed identity permissions.

### Multi-Team Patterns

To provision multiple teams:

1. Run shared infrastructure provisioning once
2. Run team workspace provisioning for each team with unique `azure_ml_team_name`
3. Platform admin manually assigns team members to workspace RBAC roles
4. Teams access workspaces independently at https://ml.azure.com

Teams share Key Vault, ACR, and App Insights. Each team has isolated workspace, storage, and compute.
