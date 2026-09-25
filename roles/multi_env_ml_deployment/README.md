# Multi-Environment ML Deployment Role

An Ansible role that automates multi-environment Azure Machine Learning deployments with automated promotion gates. Implements a hub-and-spoke architecture with shared infrastructure and environment-specific ML workspaces (dev, staging, prod).

## Description

This role automates the deployment and lifecycle management of Azure ML models across multiple environments with:

- **Shared Infrastructure**: Centralized Key Vault, Container Registry, ML Registry, Application Insights, and audit storage
- **Environment-Specific Workspaces**: Isolated ML workspaces per environment (dev, staging, prod) with dedicated storage and compute
- **Automated Promotion Gates**: Accuracy threshold validation and manual approval workflow integration
- **Audit Trail**: All deployment and promotion events logged to Azure Storage with correlation tracking
- **Governance Controls**: Per-environment network policies, compute limits, and approval requirements

## Requirements

- Ansible >= 2.16
- Python >= 3.9
- Azure collection: `azure.azcollection >= 3.20.0`
- Azure CLI configured with valid credentials
- Azure subscription with appropriate permissions

## Role Variables

### Operation Selection

```yaml
operation: provision_shared_infrastructure  # provision_shared_infrastructure | provision_environment | promote_model | delete_environment | delete_shared_infrastructure
```

### Operations

| Operation | Description |
|-----------|-------------|
| `provision_shared_infrastructure` | Creates shared resources (Key Vault, ACR, ML Registry, App Insights, audit storage) |
| `provision_environment` | Creates environment-specific workspace, storage, and compute for the specified environment |
| `promote_model` | Promotes a model from one environment to the next with gate validation |
| `delete_environment` | Removes environment-specific resources for the specified environment |
| `delete_shared_infrastructure` | Removes all shared infrastructure (WARNING: affects all environments) |

### Shared Infrastructure

```yaml
azure_region: eastus
azure_resource_group: ""  # Required: resource group for all resources

# Tags (applied to all resources)
azure_ml_menv_environment_tag: production
azure_ml_menv_cost_center: ml-platform
azure_ml_menv_team: ml-platform
azure_ml_menv_tags:
  environment: "{{ azure_ml_menv_environment_tag }}"
  cost_center: "{{ azure_ml_menv_cost_center }}"
  team: "{{ azure_ml_menv_team }}"
```

### Environment Configuration

The `azure_ml_menv_environments` dictionary defines governance policies per environment:

```yaml
azure_ml_menv_environments:
  dev:
    code: dev
    public_network_access: Enabled
    compute_max_nodes: 4
    requires_approval: false
  staging:
    code: stg
    public_network_access: Disabled
    compute_max_nodes: 2
    requires_approval: true
  prod:
    code: prod
    public_network_access: Disabled
    compute_max_nodes: 2
    requires_approval: true
```

- **code**: Short environment identifier used in resource naming
- **public_network_access**: Network policy for ML workspace (Enabled/Disabled)
- **compute_max_nodes**: Maximum nodes for auto-scaling compute cluster
- **requires_approval**: Whether manual approval is required for promotion to this environment

### Environment-Specific Operations

```yaml
azure_ml_menv_environment: dev  # dev | staging | prod
```

This variable selects the active environment for `provision_environment`, `promote_model`, and `delete_environment` operations.

### Model Promotion Gates

```yaml
# Automated gate
azure_ml_menv_min_accuracy: 0.90  # Promotion fails if model accuracy < threshold

# Manual approval gate
azure_ml_menv_promotion_approved: false  # Set to true by AAP workflow node for manual approval
```

The `promote_model` operation validates both gates:
1. **Accuracy Gate**: Model metadata must include accuracy >= `azure_ml_menv_min_accuracy`
2. **Approval Gate**: For environments with `requires_approval: true`, `azure_ml_menv_promotion_approved` must be set to `true` (typically via AAP survey/workflow)

### Model Configuration

```yaml
azure_ml_menv_model_name: menv-model
azure_ml_menv_model_version: "1"
azure_ml_menv_use_registry: true  # Publish to shared ML registry (best-effort)
```

### Audit Trail

All operations write audit events to the shared audit storage account:

```yaml
azure_ml_menv_audit_storage_account: "{{ (azure_resource_group | regex_replace('[^a-z0-9]', ''))[:15] }}auditml"
azure_ml_menv_audit_container: audit
azure_ml_menv_actor: "{{ lookup('ansible.builtin.env', 'AZURE_CLIENT_ID') | default('unknown', true) }}"
azure_ml_menv_correlation_id: "{{ now(true, '%Y%m%dT%H%M%SZ') }}"
```

Audit events include:
- Operation type and timestamp
- Actor (service principal or user)
- Correlation ID for tracing related operations
- Environment and resource details
- Promotion gate validation results

## Dependencies

None. This role uses `azure.azcollection` modules directly.

## Example Playbooks

### Provision Shared Infrastructure

```yaml
- name: Setup shared ML infrastructure
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: multi_env_ml_deployment
      vars:
        operation: provision_shared_infrastructure
        azure_resource_group: ml-deployment-rg
        azure_region: eastus
        azure_ml_menv_environment_tag: production
        azure_ml_menv_cost_center: ml-platform
        azure_ml_menv_team: ml-platform
```

### Provision Environment

```yaml
- name: Create dev ML workspace
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: multi_env_ml_deployment
      vars:
        operation: provision_environment
        azure_resource_group: ml-deployment-rg
        azure_ml_menv_environment: dev
```

### Promote Model

```yaml
- name: Promote model from dev to staging
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: multi_env_ml_deployment
      vars:
        operation: promote_model
        azure_resource_group: ml-deployment-rg
        azure_ml_menv_environment: staging  # Target environment
        azure_ml_menv_model_name: menv-model
        azure_ml_menv_model_version: "1"
        azure_ml_menv_min_accuracy: 0.90
        azure_ml_menv_promotion_approved: true  # Set by AAP for staging/prod
```

### Delete Environment

```yaml
- name: Remove staging environment
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: multi_env_ml_deployment
      vars:
        operation: delete_environment
        azure_resource_group: ml-deployment-rg
        azure_ml_menv_environment: staging
```

### Delete Shared Infrastructure

```yaml
- name: Teardown entire ML deployment platform
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: multi_env_ml_deployment
      vars:
        operation: delete_shared_infrastructure
        azure_resource_group: ml-deployment-rg
```

## AAP Integration

This role is designed for use with Ansible Automation Platform workflows:

1. **Initial Setup**: Run `provision_shared_infrastructure` once
2. **Environment Provisioning**: Use AAP job template with survey to provision dev/staging/prod environments
3. **Model Promotion**: Use AAP workflow template with approval node:
   - Job 1: Validate model meets accuracy threshold
   - Approval Node: Manual approval for staging/prod
   - Job 2: Run `promote_model` with `azure_ml_menv_promotion_approved: true`

## Architecture

### Hub-and-Spoke Model

```
┌─────────────────────────────────────────────────────────┐
│            Shared Infrastructure (Hub)                  │
│  ┌──────────┐ ┌─────┐ ┌────────────┐ ┌──────────────┐  │
│  │Key Vault │ │ ACR │ │ML Registry │ │Audit Storage │  │
│  └──────────┘ └─────┘ └────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────┘
         │              │              │              │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │   Dev   │    │ Staging │    │  Prod   │
    │Workspace│───▶│Workspace│───▶│Workspace│
    │         │    │         │    │         │
    │  Gate:  │    │  Gate:  │    │  Gate:  │
    │  None   │    │ Approval│    │ Approval│
    └─────────┘    └─────────┘    └─────────┘
```

### Promotion Flow

Models flow from dev → staging → prod with increasing governance:

1. **Dev**: No approval required, public network access enabled, higher compute limits
2. **Staging**: Requires manual approval, private network, controlled compute limits
3. **Prod**: Requires manual approval, private network, controlled compute limits

Each promotion validates:
- Model accuracy meets threshold
- Manual approval granted (for staging/prod)
- All validation results logged to audit storage

### Governance Model

- **Network Isolation**: Staging and prod use `public_network_access: Disabled`
- **Compute Limits**: Per-environment max node controls via `compute_max_nodes`
- **Approval Workflow**: `requires_approval` enforces manual gate for production environments
- **Audit Trail**: All operations logged with actor, correlation ID, and gate results
- **Resource Tagging**: Consistent tagging for cost allocation and resource tracking

## Testing

Integration tests are provided in `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/`.

Run tests:
```bash
ansible-test integration azure_ops_test_multi_env_ml_deployment --docker
```

## License

GPL-3.0-or-later

## Author Information

Created for the cloud.azure_ops collection by the Red Hat Community of Practice.

Reference Architecture: [ACA-5889](https://redhat.atlassian.net/browse/ACA-5889)
