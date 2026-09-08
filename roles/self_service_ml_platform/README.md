# Self-Service ML Platform Role

An Ansible role that enables self-service machine learning workspace provisioning on Azure through Ansible Automation Platform (AAP). Implements a hub-and-spoke architecture with centralized shared infrastructure and isolated team workspaces.

## Description

This role automates the deployment and management of an Azure Machine Learning platform with:

- **Hub Infrastructure**: Shared Key Vault, Container Registry, and Application Insights
- **Spoke Workspaces**: Isolated ML workspaces per team with dedicated storage and compute
- **Cost Controls**: Budget alerts, scale-to-zero compute, and consumption tracking
- **Security**: Identity-based authentication, RBAC, and no stored credentials

## Requirements

- Ansible >= 2.15
- Python >= 3.9
- Azure collection: `azure.azcollection >= 3.20.0`
- Azure CLI configured with valid credentials
- Azure subscription with appropriate permissions

## Role Variables

### Operation Selection

```yaml
operation: provision_shared_infrastructure  # provision_shared_infrastructure | provision_team_workspace | delete_team_workspace | delete_shared_infrastructure
```

### Shared Infrastructure (Hub)

```yaml
azure_region: eastus
azure_ml_platform_shared_rg: ml-platform-shared
azure_ml_platform_keyvault: ml-platform-kv-001  # Must be globally unique
azure_ml_platform_acr: mlplatformacr001  # Must be globally unique
azure_ml_platform_appinsights: ml-platform-insights
azure_ml_platform_admin_email: admin@example.com
azure_ml_platform_environment: production
azure_ml_platform_cost_center: ml-platform
```

### Team Workspace (Spoke)

```yaml
azure_ml_team_name: ""  # Required: 3-20 lowercase alphanumeric/hyphens
azure_ml_team_contact_email: ""  # Required: valid email
azure_ml_team_budget_limit: 2500  # Monthly budget in USD
azure_ml_team_compute_vm_size: Standard_DS3_v2
azure_ml_team_compute_max_nodes: 4
```

Computed variables (auto-generated from team name):
- `azure_ml_team_storage_account`
- `azure_ml_team_workspace_name`
- `azure_ml_team_compute_name`
- `azure_ml_team_datastore_name`
- `azure_ml_team_environment_name`

## Dependencies

- `cloud.azure_ops.azure_manage_resource_group`
- `cloud.azure_ops.azure_manage_storage_account`

## Example Playbooks

### Provision Shared Infrastructure

```yaml
- name: Setup ML platform hub infrastructure
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: self_service_ml_platform
      vars:
        operation: provision_shared_infrastructure
        azure_region: eastus
        azure_ml_platform_admin_email: platform-admin@example.com
```

### Provision Team Workspace

```yaml
- name: Create ML workspace for data science team
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: self_service_ml_platform
      vars:
        operation: provision_team_workspace
        azure_ml_team_name: data-science
        azure_ml_team_contact_email: ds-team@example.com
        azure_ml_team_budget_limit: 5000
        azure_ml_team_compute_vm_size: Standard_NC6
        azure_ml_team_compute_max_nodes: 8
```

### Delete Team Workspace

```yaml
- name: Remove ML workspace for completed project
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: self_service_ml_platform
      vars:
        operation: delete_team_workspace
        azure_ml_team_name: data-science
```

### Delete Shared Infrastructure

```yaml
- name: Teardown entire ML platform
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: self_service_ml_platform
      vars:
        operation: delete_shared_infrastructure
```

## AAP Integration

This role is designed for use with Ansible Automation Platform surveys. Example survey configurations are provided in:

- `docs/aap_surveys/platform_setup_survey.json` - Shared infrastructure setup
- `docs/aap_surveys/request_workspace_survey.json` - Team workspace provisioning

See `docs/aap_surveys/workflow_templates.md` for complete AAP setup instructions.

## Architecture

### Hub-and-Spoke Model

```
┌─────────────────────────────────────────────┐
│         Shared Infrastructure (Hub)         │
│  ┌──────────────┐  ┌─────┐  ┌────────────┐ │
│  │  Key Vault   │  │ ACR │  │ App Insights│ │
│  └──────────────┘  └─────┘  └────────────┘ │
└─────────────────────────────────────────────┘
         │              │              │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │ Team A  │    │ Team B  │    │ Team C  │
    │Workspace│    │Workspace│    │Workspace│
    └─────────┘    └─────────┘    └─────────┘
```

### Cost Control Strategy

- Budget alerts at 50%, 80%, 100% thresholds
- Email notifications to team contacts and platform admin
- Scale-to-zero compute clusters (min_instances: 0)
- 5-minute idle timeout before scale-down
- Resource tagging for cost allocation

### Security Model

- System-assigned managed identities (no credentials)
- RBAC role assignments:
  - AcrPull for container registry access
  - Key Vault Secrets User for secrets access
  - Storage Blob Data Contributor for data access
- Identity-based datastore authentication

## Testing

Integration tests are provided in `tests/integration/targets/azure_ops_test_self_service_ml_platform/`.

Run tests:
```bash
ansible-test integration azure_ops_test_self_service_ml_platform --docker
```

## License

GPL-3.0-or-later

## Author Information

Created for the cloud.azure_ops collection by the Red Hat Community of Practice.

Reference Architecture: [ACA-5887](https://redhat.atlassian.net/browse/ACA-5887)
