## cloud.azure_ops.multi_env_ml_deployment playbook

A playbook to automate multi-environment Azure Machine Learning deployment with gated model promotion from development through staging to production.

This reference architecture demonstrates how Ansible Automation Platform (AAP) orchestrates the ML deployment lifecycle with hub-and-spoke infrastructure, automated accuracy gates, manual approval nodes, and complete audit trails for compliance.

### Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      Shared Hub (Single RG)                         │
│                                                                    │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │  Key Vault   │  │  ML Registry  │  │  Audit Storage        │   │
│  │  (Secrets)   │  │  (Cross-WS)   │  │  (Immutable Blob)     │   │
│  └──────────────┘  └───────────────┘  └───────────────────────┘   │
│                                                                    │
│  ┌──────────────┐  ┌───────────────┐                              │
│  │     ACR      │  │ App Insights  │                              │
│  │  (Images)    │  │  (Telemetry)  │                              │
│  └──────────────┘  └───────────────┘                              │
└────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Dev Spoke      │  │ Staging Spoke   │  │  Prod Spoke     │
│                 │  │                 │  │                 │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ Workspace │  │  │  │ Workspace │  │  │  │ Workspace │  │
│  │ (Public)  │  │  │  │ (Private) │  │  │  │ (Private) │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ Storage   │  │  │  │ Storage   │  │  │  │ Storage   │  │
│  │ (4 nodes) │  │  │  │ (2 nodes) │  │  │  │ (2 nodes) │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ Compute   │  │  │  │ Compute   │  │  │  │ Compute   │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    ▲                    ▲
         │                    │                    │
         └──────[Promote]─────┴──────[Promote]─────┘
            (Accuracy Gate +       (Accuracy Gate +
             No Approval)           Manual Approval)
```

#### Promotion Flow

Model promotion follows a gated path through three environments with two promotion hops:

```
┌─────────┐     Gate 1              ┌──────────┐     Gate 2              ┌──────────┐
│   Dev   │────────────────────────▶│ Staging  │────────────────────────▶│   Prod   │
└─────────┘                         └──────────┘                         └──────────┘
            1. Accuracy ≥ threshold              1. Accuracy ≥ threshold
            2. No approval required              2. Manual approval required
            3. Audit record                      3. Audit record
```

**Gate Sequence (per promotion hop):**

1. **Automated Accuracy Gate**: Model `accuracy` tag must meet or exceed `azure_ml_menv_min_accuracy` (default 0.90)
2. **Manual Approval Gate** (staging/prod only): AAP approval node sets `azure_ml_menv_promotion_approved=true`
3. **Model Registration**: Promoted model registered in target workspace and shared ML registry
4. **Audit Record**: Immutable audit event written to blob storage with timestamp, actor, approval status, and gate result

### Environment Configuration

The `azure_ml_menv_environments` variable defines governance policies per environment:

| Field | Type | Description | Dev | Staging | Prod |
|-------|------|-------------|-----|---------|------|
| `code` | string | Short environment code (used in resource names) | `dev` | `stg` | `prod` |
| `public_network_access` | string | Workspace network access (`Enabled` or `Disabled`) | `Enabled` | `Disabled` | `Disabled` |
| `compute_max_nodes` | integer | Maximum compute cluster nodes | `4` | `2` | `2` |
| `requires_approval` | boolean | Whether manual approval is required for promotion to this environment | `false` | `true` | `true` |

**Example:**

```yaml
azure_ml_menv_environments:
  dev:     { code: dev,  public_network_access: Enabled,  compute_max_nodes: 4, requires_approval: false }
  staging: { code: stg,  public_network_access: Disabled, compute_max_nodes: 2, requires_approval: true }
  prod:    { code: prod, public_network_access: Disabled, compute_max_nodes: 2, requires_approval: true }
```

### Promotion Gates

#### Automated Accuracy Gate

The playbook enforces a minimum accuracy threshold (`azure_ml_menv_min_accuracy`, default `0.90`) for all promotions. The gate:

1. Looks up the candidate model in the source workspace
2. Extracts the `accuracy` tag from model metadata
3. Fails promotion if `accuracy < azure_ml_menv_min_accuracy`
4. Records gate result (`passed` or `failed`) in the audit trail

**Variable:**

* **azure_ml_menv_min_accuracy**: Minimum model accuracy (0.0-1.0). Default: `0.90`

#### Manual Approval Gate

Staging and production environments require manual approval (`requires_approval: true`). The gate:

1. Checks the target environment's `requires_approval` flag
2. Fails promotion if `azure_ml_menv_promotion_approved != true`
3. Records approval status (`approved`, `not_required`, or `denied`) in audit trail

**AAP Integration:**

In an AAP workflow, the approval node precedes the promotion job template and sets the approval variable:

```yaml
azure_ml_menv_promotion_approved: true
```

Without AAP, manually set this variable when invoking the playbook for staging/prod promotions.

### Audit Trail

All provisioning and promotion actions are recorded in a **tamper-evident** audit trail stored in Azure Blob Storage. Each event writes one immutable JSON blob that is never mutated, with a unique name incorporating timestamp, action type, environment, and a random token.

**Blob Naming Convention:**

```
audit/<timestamp>-<action>-<environment>-<uniq>.json
```

Example: `audit/20260918T143022-promote-staging-a3f2c8e1.json`

**Audit Record Fields:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO 8601 | Action timestamp (human-readable) | `2026-09-18T14:30:22Z` |
| `action` | string | Action type | `promote`, `promote_rejected`, `provision_shared`, `provision_environment`, `delete_environment`, `delete_shared` |
| `environment` | string | Target environment (for environment-scoped actions) | `staging`, `prod` |
| `model_name` | string | Model name (for model actions) | `menv-model` |
| `model_version` | string | Model version | `1` |
| `actor` | string | Service principal or user identity | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `approval_status` | string | Manual approval status | `approved`, `not_required`, `denied`, `not_evaluated` |
| `gate_result` | string | Automated gate result | `passed`, `failed`, `skipped` |
| `correlation_id` | string | Correlation ID for related actions | `20260918T143022-12345678` |

**Audit Actions:**

- `provision_shared`: Shared hub infrastructure provisioned
- `provision_environment`: Environment-specific spoke resources provisioned
- `promote`: Model successfully promoted to target environment
- `promote_rejected`: Promotion blocked by a gate (accuracy or approval)
- `delete_environment`: Environment resources deleted
- `delete_shared`: Shared hub infrastructure deleted

**Tamper-Evident Design:**

The audit trail provides tamper-evidence through:

* One immutable blob per event (never updated after creation)
* Unique blob names prevent same-second overwrites
* Correlation IDs link related events across a single run
* Timestamp and actor tracking for forensic analysis

**Production Hardening:**

For true tamper-proof retention meeting regulatory compliance requirements (SOC2, HIPAA, FedRAMP), enable an **Azure Storage immutability policy (WORM)** or **legal hold** on the audit container post-deployment. This prevents deletion or modification of audit blobs for a defined retention period. See [Azure Blob immutable storage](https://learn.microsoft.com/azure/storage/blobs/immutable-storage-overview) for configuration guidance.

### Network Isolation

Environments use different network access policies to balance development velocity with production security:

| Environment | Public Network Access | Rationale |
|-------------|----------------------|-----------|
| Dev | `Enabled` | Allows rapid experimentation, local development, and notebook access |
| Staging | `Disabled` | Enforces production-like network constraints for testing |
| Prod | `Disabled` | Isolates production workloads from public internet |

**Private Endpoint Pattern (Staging/Prod):**

For production deployments, implement private connectivity for staging and prod workspaces:

1. **Private Endpoint**: Create a private endpoint for each workspace in a dedicated VNet
2. **VNet Peering**: Peer workspace VNets with hub VNet containing shared resources (ACR, Key Vault, storage)
3. **Private DNS Zones**: Configure private DNS zones for Azure ML API endpoints:
   - `privatelink.api.azureml.ms`
   - `privatelink.notebooks.azure.net`
   - `privatelink.blob.core.windows.net` (for storage accounts)
4. **NSG Rules**: Lock down compute clusters to allow only workspace-managed traffic
5. **Managed VNet**: Enable workspace managed virtual network (`managed_network: allow_only_approved_outbound`) for automatic private endpoint provisioning

This pattern is documented as guidance — the playbook provisions workspaces with `public_network_access: Disabled` but does not provision private endpoints or VNet infrastructure. Implement private connectivity post-deployment via Azure networking resources or separate automation.

### Prerequisites

* Azure subscription with sufficient quota for ML compute
* `azure.azcollection` >= 3.20.0 installed (for ML registry support)
* Azure credentials configured (service principal, managed identity, or CLI auth)
* The following Azure resource providers must be registered on the subscription:
  - `Microsoft.MachineLearningServices`
  - `Microsoft.Storage`
  - `Microsoft.KeyVault`
  - `Microsoft.ContainerRegistry`
  - `Microsoft.Insights`

### Variables

#### Common

* **azure_resource_group**: (Required) Resource group for all resources (hub and spokes). **Note:** shared and per-environment resource names are derived from this value, so use only letters, digits, and hyphens (DNS-safe characters). Resource group names containing underscores or periods can yield invalid Key Vault, ML registry, or workspace names.
* **azure_region**: Azure location for resources. Default: `eastus`
* **operation**: Operation to perform. Valid values: `provision_shared_infrastructure`, `provision_environment`, `promote_model`, `delete_environment`, `delete_shared_infrastructure`. Required when using the role directly (playbook sets this automatically).
* **menv_operation**: Playbook-level operation selector. Valid values: `all` (full lifecycle demo), `provision_shared_infrastructure`, `provision_environment`, `register_model`, `promote_model`, `delete_environment`, `delete_shared_infrastructure`. Default: `all` (AAP job templates set this to run a single operation).
* **azure_ml_menv_environment**: Active environment for environment-scoped operations (`dev`, `staging`, `prod`). Default: `dev`

#### Shared Infrastructure (Hub)

* **azure_ml_menv_keyvault_name**: Key Vault name (globally unique, 3-24 chars). Default: `{{ azure_resource_group[:19] }}-mkv` (max 23 chars)
* **azure_ml_menv_acr_name**: Container Registry name (globally unique, 5-50 alphanumeric chars). Default: `{{ (azure_resource_group | regex_replace('[^a-z0-9]', ''))[:43] }}menvacr` (max 50 chars)
* **azure_ml_menv_appinsights_name**: Application Insights name. Default: `{{ azure_resource_group }}-menv-ai`
* **azure_ml_menv_registry_name**: ML registry name for cross-workspace model sharing. Default: `{{ azure_resource_group[:20] }}-menvreg` (max 28 chars)
* **azure_ml_menv_audit_storage_account**: Storage account for audit trail (alphanumeric only). Default: `{{ (azure_resource_group | regex_replace('[^a-z0-9]', ''))[:15] }}auditml` (max 22 chars)
* **azure_ml_menv_audit_container**: Blob container name for audit records. Default: `audit`
* **azure_ml_menv_use_registry**: Whether to publish models to the ML registry (best-effort). Default: `true`

#### Per-Environment Resources (Spokes)

* **azure_ml_menv_storage_account**: Environment storage account name (max 24 chars, alphanumeric only, auto-suffixed with env code). Default: derived from `azure_resource_group` with `<code>ml` suffix
* **azure_ml_menv_workspace_name**: ML workspace name (auto-suffixed with env code). Default: `{{ azure_resource_group[:22] }}-ml-<code>`
* **azure_ml_menv_compute_name**: Compute cluster name (max 16 chars, must start with a letter, unique per workspace within the resource group). Default: `<code>-<sanitized-rg[:11]>` — the env-code prefix keeps dev/staging/prod distinct and the resource-group token keeps separate deployments distinct
* **azure_ml_menv_compute_vm_size**: VM size for compute nodes. Default: `Standard_DS3_v2`
* **azure_ml_menv_storage_container**: Blob container for training data. Default: `training-data`

#### Model and Promotion

* **azure_ml_menv_model_name**: Model name. Default: `menv-model`
* **azure_ml_menv_model_version**: Model version. Default: `1`
* **azure_ml_menv_min_accuracy**: Minimum accuracy threshold for automated gate (0.0-1.0). Default: `0.90`
* **azure_ml_menv_promotion_approved**: Manual approval gate (AAP node supplies `true`). Default: `false`
* **azure_ml_menv_promote_source**: Source environment for promotion (used with `operation=promote_model`). No default.
* **azure_ml_menv_promote_target**: Target environment for promotion (used with `operation=promote_model`). No default.

#### Tags and Audit Context

* **azure_ml_menv_environment_tag**: Environment tag for all resources. Default: `production`
* **azure_ml_menv_cost_center**: Cost center tag. Default: `ml-platform`
* **azure_ml_menv_team**: Team tag. Default: `ml-platform`
* **azure_ml_menv_actor**: Actor identity for audit trail. Default: `{{ lookup('ansible.builtin.env', 'AZURE_CLIENT_ID') }}`
* **azure_ml_menv_correlation_id**: Correlation ID for audit trail. Default: `{{ now(true, '%Y%m%dT%H%M%SZ') }}`

### Usage

#### Provision Full Multi-Environment Infrastructure

```bash
ansible-playbook cloud.azure_ops.multi_env_ml_deployment \
  -e azure_resource_group=my-ml-platform-rg \
  -e azure_region=eastus
```

This runs the full lifecycle:

1. Provision shared hub infrastructure (KV, ACR, App Insights, audit storage, ML registry)
2. Provision dev, staging, and prod environments (workspace, storage, compute)
3. Register initial model in dev workspace
4. Promote model dev → staging (automated gate + approval gate)
5. Promote model staging → prod (automated gate + approval gate)

#### Provision Shared Infrastructure Only

```bash
ansible-playbook cloud.azure_ops.multi_env_ml_deployment \
  -e azure_resource_group=my-ml-platform-rg \
  -e menv_operation=provision_shared_infrastructure
```

**Note:** The playbook uses `menv_operation` to select which operation(s) to run. Omit it (or set `menv_operation=all`) to run the full lifecycle demo. AAP job templates set `menv_operation` to run a single operation.

#### Provision Single Environment

```bash
ansible-playbook cloud.azure_ops.multi_env_ml_deployment \
  -e azure_resource_group=my-ml-platform-rg \
  -e menv_operation=provision_environment \
  -e azure_ml_menv_environment=staging
```

#### Promote Model with Custom Accuracy Threshold

```bash
ansible-playbook cloud.azure_ops.multi_env_ml_deployment \
  -e azure_resource_group=my-ml-platform-rg \
  -e menv_operation=promote_model \
  -e azure_ml_menv_promote_source=dev \
  -e azure_ml_menv_promote_target=staging \
  -e azure_ml_menv_min_accuracy=0.95 \
  -e azure_ml_menv_promotion_approved=true
```

#### Teardown Single Environment

```bash
ansible-playbook cloud.azure_ops.multi_env_ml_deployment \
  -e azure_resource_group=my-ml-platform-rg \
  -e menv_operation=delete_environment \
  -e azure_ml_menv_environment=dev
```

#### Teardown All Infrastructure

```bash
ansible-playbook cloud.azure_ops.multi_env_ml_deployment \
  -e azure_resource_group=my-ml-platform-rg \
  -e menv_operation=delete_shared_infrastructure
```

**Warning:** This deletes the hub (KV, ACR, registry, audit storage) and all three spoke environments. Audit records are preserved in the storage account until explicitly deleted.

### AAP Workflow Integration

See `docs/aap_surveys/multi_env_ml_workflow.md` for AAP workflow template configuration with approval nodes and survey definitions.

### Security Best Practices

The playbook deploys with system-assigned managed identity and RBAC-enabled Key Vault. For production deployments, consider:

* **RBAC Role Assignments**: Assign `AzureML Data Scientist` to ML workspace users. Assign `AcrPull` to workspace managed identity on the Container Registry. Use `Storage Blob Data Contributor` instead of storage account keys for datastore access.
* **Private Endpoints**: Implement the private endpoint pattern documented in the Network Isolation section for staging and prod workspaces.
* **Network Isolation**: Deploy workspaces with managed virtual network (`managed_network: allow_only_approved_outbound`). Create private endpoints for storage, Key Vault, and ACR.
* **Key Vault Integration**: Store model deployment credentials and API keys in Key Vault rather than environment variables.
* **Model Governance**: Use model stages (`Development`, `Staging`, `Production`) in the ML registry to gate promotion. Integrate approval gates in AAP workflows.
* **Audit Retention**: Configure blob lifecycle management to archive audit records after 90 days or per compliance requirements.

### Troubleshooting

* **Shared infrastructure provisioning fails**: Ensure all required resource providers are registered. Check that Key Vault, ACR, and audit storage account names are globally unique and follow naming constraints.
* **Environment provisioning fails**: Verify shared infrastructure exists in the resource group. Check that workspace names are globally unique.
* **Compute cluster stuck provisioning**: Verify VM quota available in the target region. Check Azure portal for quota increase requests.
* **Accuracy gate fails**: Review model `accuracy` tag in the source workspace. Ensure the tag is set correctly by training jobs or manually. Lower `azure_ml_menv_min_accuracy` if testing with dummy models.
* **Approval gate fails**: Set `azure_ml_menv_promotion_approved=true` when invoking the playbook manually. In AAP workflows, the approval node sets this automatically.
* **Model not found in registry**: Verify the ML registry was created with `azure_ml_menv_use_registry=true`. Check that the service principal has `Storage Blob Data Contributor` on the registry backing storage account.
* **Audit record not written**: Verify the audit storage account and container exist. Check that the service principal has `Storage Blob Data Contributor` on the audit storage account.
* **Private workspace connectivity fails**: Ensure private endpoints and private DNS zones are configured per the Network Isolation section. The playbook does not provision these automatically.
