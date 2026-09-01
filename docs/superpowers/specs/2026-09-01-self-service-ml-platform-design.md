# Self-Service ML Platform with AAP - Design Specification

**Jira:** ACA-5887  
**Date:** 2026-09-01  
**Status:** Design Approved  

## Executive Summary

This reference architecture demonstrates how Ansible Automation Platform (AAP) can provide a self-service portal for data science teams to provision ML infrastructure on demand. The solution eliminates weeks-long provisioning bottlenecks by offering standardized workspace templates through AAP's survey-driven catalog, while embedding security, compliance, and cost controls into every provisioning request.

### Key Capabilities

- **Self-service provisioning** — Data scientists request ML workspaces via AAP survey, receive fully configured environment in ~10 minutes
- **Hub-and-spoke architecture** — Shared infrastructure (Key Vault, ACR, App Insights) reduces costs; isolated workspaces ensure data security
- **Built-in cost governance** — Budget alerts, auto-shutdown compute, cost allocation tags on every resource
- **Multi-team isolation** — Each team gets dedicated workspace + storage while sharing common platform resources
- **Production-ready security** — RBAC-enabled Key Vault, managed identity authentication, no exposed credentials

### User Stories Addressed

1. **As a data scientist**, I want to request an ML workspace through a self-service catalog so that I can start experimenting within minutes instead of waiting weeks
2. **As a platform administrator**, I want standardized ML environment templates so that every provisioned workspace meets our security and compliance requirements
3. **As a finance manager**, I want automated cost controls on ML workspaces so that teams cannot accidentally provision expensive GPU clusters without approval

---

## Architecture

### High-Level Design

The platform uses a **hub-and-spoke model** where shared infrastructure (hub) is provisioned once by platform admins, and team workspaces (spokes) are self-service provisioned on-demand through AAP surveys.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AAP Self-Service Catalog                          │
│                                                                      │
│  ┌────────────────────┐         ┌──────────────────────────────┐   │
│  │ Platform Setup     │         │ Request ML Workspace         │   │
│  │ (Admin, One-time)  │         │ (Self-Service, Repeatable)   │   │
│  │                    │         │                              │   │
│  │ Survey:            │         │ Survey:                      │   │
│  │ - Azure region     │         │ - Team name                  │   │
│  │ - Shared RG name   │         │ - Budget limit               │   │
│  └────────┬───────────┘         │ - Compute (VM size, nodes)   │   │
│           │                     │ - Data access scope          │   │
│           │                     └────────┬─────────────────────┘   │
│           │                              │                         │
└───────────┼──────────────────────────────┼─────────────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│            self_service_ml_platform.yml Playbook                      │
│                                                                       │
│  operation=provision_shared_infrastructure  │  operation=provision_  │
│                                              │  team_workspace        │
└───────────────────────────────────────────────────────────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────┐         ┌──────────────────────────────┐
│  Shared Hub         │         │  Team Workspace (Isolated)   │
│  (One per platform) │◄────────┤  (One per team)              │
│                     │         │                              │
│  ┌──────────────┐   │         │  ┌────────────────────────┐  │
│  │ Key Vault    │   │         │  │ ML Workspace           │  │
│  │ (Secrets)    │◄──┼─────────┼──┤ - Managed Identity     │  │
│  └──────────────┘   │         │  │ - Private RBAC         │  │
│                     │         │  └────────────────────────┘  │
│  ┌──────────────┐   │         │                              │
│  │ ACR          │   │         │  ┌────────────────────────┐  │
│  │ (Images)     │◄──┼─────────┼──┤ Storage Account        │  │
│  └──────────────┘   │         │  │ - Team data only       │  │
│                     │         │  │ - Cost tracking tags   │  │
│  ┌──────────────┐   │         │  └────────────────────────┘  │
│  │ App Insights │   │         │                              │
│  │ (Monitoring) │◄──┼─────────┼──┤ Compute Cluster          │  │
│  └──────────────┘   │         │  │ - Auto-shutdown          │  │
│                     │         │  │ - Min=0 (scale-to-zero)  │  │
└─────────────────────┘         │  │ - Budget-aware sizing    │  │
                                │  └────────────────────────┘  │
                                │                              │
                                │  ┌────────────────────────┐  │
                                │  │ Datastore + Dataset    │  │
                                │  │ - Pre-configured       │  │
                                │  └────────────────────────┘  │
                                │                              │
                                │  ┌────────────────────────┐  │
                                │  │ Base Environment       │  │
                                │  │ - Scikit-learn + Pandas│  │
                                │  └────────────────────────┘  │
                                └──────────────────────────────┘
```

### Design Principles

1. **Shared infrastructure = cost efficiency** — Key Vault, ACR, App Insights shared across all teams (eliminate per-team overhead)
2. **Isolated workspaces = data security** — Each team's data, models, and compute fully isolated (no cross-team access)
3. **Cost visibility = governance** — Every resource tagged with team name for chargeback reports
4. **Self-service = speed** — Workspace provisioned in ~5-10 minutes via AAP survey (eliminate manual ticketing)
5. **Approval gates = control** — Requests over budget threshold require manager approval before provisioning

---

## Components

### 1. Shared Infrastructure (Hub)

**Purpose:** Platform-wide resources that all teams share, provisioned once by platform administrators.

#### Resources

##### Resource Group
- **Name:** `azure_ml_platform_shared_rg` (default: `ml-platform-shared`)
- **Purpose:** Container for all shared infrastructure
- **Lifecycle:** Created in platform setup, deleted when platform is decommissioned

##### Key Vault
- **Name:** `azure_ml_platform_keyvault` (globally unique)
- **Purpose:** Centralized secret storage for connection strings, API keys, certificates
- **Configuration:**
  - RBAC-enabled (`enable_rbac_authorization: true`)
  - SKU: Standard
  - Soft delete enabled (90-day recovery window)
- **Access Control:**
  - Workspace managed identities granted `Key Vault Secrets User` role
  - Platform admins granted `Key Vault Administrator` role

##### Container Registry (ACR)
- **Name:** `azure_ml_platform_acr` (globally unique, alphanumeric only)
- **Purpose:** Shared Docker images for ML environments
- **Configuration:**
  - SKU: Standard
  - Admin user disabled (use managed identity)
  - Common base images: Python data science, PyTorch, TensorFlow, scikit-learn
- **Access Control:**
  - Workspace managed identities granted `AcrPull` role
  - CI/CD service principal granted `AcrPush` role

##### Application Insights
- **Name:** `azure_ml_platform_appinsights`
- **Purpose:** Centralized monitoring and logging for all workspaces
- **Configuration:**
  - Application type: web
  - All workspaces send telemetry here
  - Platform admin can monitor cross-team metrics and quotas

#### Variables

```yaml
# Shared Infrastructure Variables
azure_ml_platform_shared_rg: "ml-platform-shared"
azure_region: "eastus"
azure_ml_platform_keyvault: "ml-platform-kv-001"  # Must be globally unique
azure_ml_platform_acr: "mlplatformacr001"  # Must be globally unique
azure_ml_platform_appinsights: "ml-platform-insights"
```

---

### 2. Team Workspace (Spoke)

**Purpose:** Isolated environment for a single team, provisioned on-demand via self-service catalog.

#### Resources

##### ML Workspace
- **Name:** `{{ azure_ml_team_name }}-ml-workspace`
- **Purpose:** Team's Azure ML workspace for experiments, jobs, models, endpoints
- **Configuration:**
  - System-assigned managed identity
  - Public network access enabled (production: use private endpoints)
  - Display name includes team name for easy identification
- **Tags:**
  - `team: {{ azure_ml_team_name }}`
  - `budget_limit: {{ azure_ml_team_budget_limit }}`
  - `provisioned_date: {{ ansible_date_time.iso8601 }}`
  - `cost_center: ml-platform`
  - `environment: production`

##### Storage Account
- **Name:** `{{ azure_ml_team_name | truncate(18, True, '') }}mlstor` (max 24 chars)
- **Purpose:** Team-specific data storage for datasets, models, artifacts
- **Configuration:**
  - Account kind: StorageV2
  - Performance: Standard
  - Replication: LRS (production: consider GRS)
  - Blob containers: `datasets`, `models`, `artifacts`
  - Lifecycle management: auto-archive data older than 90 days to Cool tier
- **Access Control:**
  - Workspace managed identity: `Storage Blob Data Contributor`
  - Team members: Access via workspace only (no direct storage access)

##### Compute Cluster
- **Name:** `{{ azure_ml_team_name }}-compute`
- **Purpose:** Auto-scaling training compute for ML jobs
- **Configuration:**
  - Type: AmlCompute (managed compute)
  - VM size: From survey input (validated against budget)
  - Min instances: `0` (scale-to-zero for cost savings)
  - Max instances: Calculated from budget limit and VM hourly rate
  - Idle time before scale down: `300` seconds (5 minutes)
  - Location: Same as workspace
- **Cost Calculation:**
  ```python
  max_nodes = min(
      survey_requested_max_nodes,
      floor(monthly_budget / (vm_hourly_rate * 730 hours))
  )
  ```

##### Datastore
- **Name:** `{{ azure_ml_team_name }}_datastore`
- **Purpose:** Registered connection to team storage account
- **Configuration:**
  - Type: AzureBlob
  - Container: `datasets`
  - Authentication: Managed identity (no account keys)
  - Set as workspace default datastore

##### Data Asset (Optional)
- **Name:** `sample-dataset` (placeholder)
- **Purpose:** Placeholder to demonstrate data registration
- **Configuration:**
  - Type: `uri_folder`
  - Path: `azureml://datastores/workspaceblobstore/paths/sample-data`
  - Teams register their own data assets post-provisioning

##### Base Environment
- **Name:** `{{ azure_ml_team_name }}-base-env`
- **Purpose:** Pre-built training environment with common ML libraries
- **Configuration:**
  - Type: Docker image
  - Image: `mcr.microsoft.com/azureml/curated/sklearn-1.5-ubuntu22.04`
  - Includes: scikit-learn 1.5, pandas, numpy, matplotlib, joblib
  - Teams can create custom environments as needed

#### Variables

```yaml
# Team Workspace Variables
azure_ml_team_name: "datascience-alpha"  # Alphanumeric, hyphens, 3-20 chars
azure_ml_team_contact_email: "ds-alpha@company.com"
azure_ml_team_budget_limit: 5000  # USD/month
azure_ml_team_compute_vm_size: "Standard_DS3_v2"  # CPU: 4 cores, 14GB RAM
azure_ml_team_compute_max_nodes: 4
azure_ml_team_data_access_scope: "restricted"  # restricted|shared|external
```

---

### 3. Cost Controls

#### Budget Alerts

**Components:**
- **Action Group** — Email notification to team contact and platform admin
- **Budget Alert Rules** — Fire at 50%, 80%, 100% of monthly budget
- **Cost Allocation Tags** — Flow through to Azure Cost Management

**Implementation:**
```yaml
- name: Create budget alert action group
  azure.azcollection.azure_rm_resource:
    resource_group: "{{ azure_resource_group }}"
    provider: insights
    resource_type: actionGroups
    resource_name: "{{ azure_ml_team_name }}-budget-alerts"
    api_version: "2023-01-01"
    body:
      location: global
      properties:
        groupShortName: "{{ azure_ml_team_name[:12] }}"
        enabled: true
        emailReceivers:
          - name: "TeamContact"
            emailAddress: "{{ azure_ml_team_contact_email }}"
          - name: "PlatformAdmin"
            emailAddress: "{{ azure_ml_platform_admin_email }}"

- name: Create budget alerts at 50%, 80%, 100%
  azure.azcollection.azure_rm_resource:
    resource_group: "{{ azure_resource_group }}"
    provider: Microsoft.Consumption
    resource_type: budgets
    resource_name: "{{ azure_ml_team_name }}-budget"
    api_version: "2023-11-01"
    body:
      properties:
        category: Cost
        amount: "{{ azure_ml_team_budget_limit }}"
        timeGrain: Monthly
        timePeriod:
          startDate: "{{ lookup('pipe', 'date +%Y-%m-01') }}"
        notifications:
          Actual_50_Percent:
            enabled: true
            operator: GreaterThan
            threshold: 50
            contactEmails:
              - "{{ azure_ml_team_contact_email }}"
          Actual_80_Percent:
            enabled: true
            operator: GreaterThan
            threshold: 80
            contactEmails:
              - "{{ azure_ml_team_contact_email }}"
              - "{{ azure_ml_platform_admin_email }}"
          Actual_100_Percent:
            enabled: true
            operator: GreaterThan
            threshold: 100
            contactEmails:
              - "{{ azure_ml_team_contact_email }}"
              - "{{ azure_ml_platform_admin_email }}"
```

#### Auto-Shutdown Policies

**Compute Cluster:**
- `min_instances: 0` — Cluster scales to zero nodes when idle
- `idle_time_before_scale_down: 300` — 5-minute idle grace period
- No scheduled shutdown needed (scale-to-zero handles this)

**Future Enhancement — Workspace Auto-Pause:**
- Azure Automation runbook to pause workspace after business hours
- Schedule: Monday-Friday 6pm - 8am, all day Saturday-Sunday
- Configurable per team via survey option

#### Cost Allocation Tagging

**Required Tags on All Resources:**
- `team: {{ azure_ml_team_name }}` — Primary cost allocation dimension
- `budget_limit: {{ azure_ml_team_budget_limit }}` — For budget tracking
- `cost_center: ml-platform` — Roll-up for platform-wide costs
- `environment: production` — Distinguish from dev/test environments
- `provisioned_date: {{ ansible_date_time.iso8601 }}` — Lifecycle tracking

**Tag Enforcement:**
- Playbook applies tags during resource creation
- Tags flow through to Azure Cost Management for chargeback reports
- Monthly cost reports generated per team via Azure Cost Management API

---

### 4. RBAC Configuration

#### Workspace-Level Roles

**Role Assignments (Manual Post-Provisioning):**

| Persona | Azure Role | Permissions |
|---------|-----------|-------------|
| Team Members (Data Scientists) | `AzureML Data Scientist` | Submit jobs, register models, create endpoints, manage compute |
| Team Lead | `AzureML Compute Operator` | All Data Scientist permissions + manage compute quotas |
| Viewers (Stakeholders) | `Reader` | Read-only access to workspace, jobs, models |
| Platform Admin | `Owner` | Full control for troubleshooting and maintenance |

**Implementation Approach:**
- Playbook documents RBAC steps in output (not automated to avoid requiring Graph API permissions)
- Platform admin manually assigns roles after provisioning
- Alternative: Use `azure_rm_roleassignment` if service principal has User Access Administrator role

#### Shared Resource Access

**Managed Identity Permissions (Automated):**

```yaml
- name: Grant workspace managed identity AcrPull on shared ACR
  azure.azcollection.azure_rm_roleassignment:
    scope: "/subscriptions/{{ azure_subscription_id }}/resourceGroups/{{ azure_ml_platform_shared_rg }}/providers/Microsoft.ContainerRegistry/registries/{{ azure_ml_platform_acr }}"
    assignee_object_id: "{{ workspace_managed_identity.principal_id }}"
    role_definition: "AcrPull"

- name: Grant workspace managed identity Key Vault Secrets User
  azure.azcollection.azure_rm_roleassignment:
    scope: "/subscriptions/{{ azure_subscription_id }}/resourceGroups/{{ azure_ml_platform_shared_rg }}/providers/Microsoft.KeyVault/vaults/{{ azure_ml_platform_keyvault }}"
    assignee_object_id: "{{ workspace_managed_identity.principal_id }}"
    role_definition: "Key Vault Secrets User"

- name: Grant workspace managed identity Storage Blob Data Contributor on team storage
  azure.azcollection.azure_rm_roleassignment:
    scope: "/subscriptions/{{ azure_subscription_id }}/resourceGroups/{{ azure_resource_group }}/providers/Microsoft.Storage/storageAccounts/{{ azure_ml_team_storage_account }}"
    assignee_object_id: "{{ workspace_managed_identity.principal_id }}"
    role_definition: "Storage Blob Data Contributor"
```

---

## AAP Self-Service Catalog Integration

### Survey 1: Platform Setup (Admin-Only)

**Purpose:** One-time setup of shared ML platform infrastructure by platform administrators.

**Survey Specification:**

```yaml
survey_name: "ML Platform - Shared Infrastructure Setup"
description: "One-time setup of shared ML platform resources (Key Vault, ACR, App Insights)"

questions:
  - variable: azure_region
    question: "Azure region for shared resources?"
    type: multiplechoice
    choices:
      - eastus
      - westus2
      - westeurope
      - centralus
    default: eastus
    required: true
  
  - variable: azure_ml_platform_shared_rg
    question: "Resource group name for shared infrastructure?"
    type: text
    default: "ml-platform-shared"
    required: true
  
  - variable: azure_ml_platform_keyvault
    question: "Key Vault name (globally unique, 3-24 chars, alphanumeric and hyphens)?"
    type: text
    required: true
    validation_regex: "^[a-zA-Z](?:[a-zA-Z0-9-]{1,22}[a-zA-Z0-9])?$"
  
  - variable: azure_ml_platform_acr
    question: "Container Registry name (globally unique, 5-50 chars, alphanumeric only)?"
    type: text
    required: true
    validation_regex: "^[a-zA-Z0-9]{5,50}$"
  
  - variable: azure_ml_platform_admin_email
    question: "Platform admin email for alerts?"
    type: text
    required: true
    validation_regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
```

**Workflow Template:** `ML Platform - Provision Shared Infrastructure`

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.self_service_ml_platform`
- Extra vars: `operation: provision_shared_infrastructure` + survey variables
- Credentials: Azure Service Principal with Contributor role
- Limit: `localhost`

---

### Survey 2: Request ML Workspace (Self-Service)

**Purpose:** Self-service provisioning of isolated ML workspace for data science teams.

**Survey Specification:**

```yaml
survey_name: "Request ML Workspace"
description: "Self-service provisioning of isolated ML workspace for your team"

questions:
  - variable: azure_ml_team_name
    question: "Team name (lowercase, alphanumeric, hyphens only, 3-20 chars)?"
    type: text
    required: true
    validation_regex: "^[a-z0-9-]{3,20}$"
    help_text: "Used for workspace name and cost tracking tags. Example: datascience-alpha"
  
  - variable: azure_ml_team_contact_email
    question: "Team contact email for budget alerts?"
    type: text
    required: true
    validation_regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  
  - variable: azure_ml_team_budget_limit
    question: "Monthly budget limit (USD)?"
    type: multiplechoice
    choices:
      - display: "$1,000/month (Development/Testing)"
        value: 1000
      - display: "$2,500/month (Small Team)"
        value: 2500
      - display: "$5,000/month (Standard Team)"
        value: 5000
      - display: "$10,000/month (Large Team - Requires Approval)"
        value: 10000
    default: 2500
    required: true
  
  - variable: azure_ml_team_compute_vm_size
    question: "Primary compute VM size?"
    type: multiplechoice
    choices:
      - display: "Standard_DS3_v2 (CPU: 4 cores, 14GB RAM) - $0.27/hr"
        value: "Standard_DS3_v2"
      - display: "Standard_DS4_v2 (CPU: 8 cores, 28GB RAM) - $0.54/hr"
        value: "Standard_DS4_v2"
      - display: "Standard_NC6s_v3 (GPU: 6 cores, 112GB RAM, 1x V100) - $3.06/hr"
        value: "Standard_NC6s_v3"
      - display: "Standard_NC12s_v3 (GPU: 12 cores, 224GB RAM, 2x V100) - $6.12/hr"
        value: "Standard_NC12s_v3"
    default: "Standard_DS3_v2"
    required: true
  
  - variable: azure_ml_team_compute_max_nodes
    question: "Maximum compute cluster nodes?"
    type: multiplechoice
    choices:
      - display: "2 nodes (Small workloads)"
        value: 2
      - display: "4 nodes (Standard workloads)"
        value: 4
      - display: "8 nodes (Large workloads)"
        value: 8
      - display: "16 nodes (Distributed training - Requires Approval)"
        value: 16
    default: 4
    required: true
  
  - variable: azure_ml_team_data_access_scope
    question: "Data access requirements?"
    type: multiplechoice
    choices:
      - display: "Restricted (Team data only, no external access)"
        value: "restricted"
      - display: "Shared (Access to shared datasets from other teams)"
        value: "shared"
      - display: "External (Private endpoints to external data sources)"
        value: "external"
    default: "restricted"
    required: true
```

**Workflow Template:** `ML Platform - Provision Team Workspace`

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.self_service_ml_platform`
- Extra vars: `operation: provision_team_workspace` + survey variables
- Credentials: Azure Service Principal with Contributor role
- Limit: `localhost`

---

### Workflow Configuration

#### Workflow 1: Provision Shared Infrastructure

**Workflow Nodes:**

```yaml
workflow_nodes:
  - node_id: 1
    name: "Pre-flight Validation"
    type: job_template
    job_template: "Validate Azure Prerequisites"
    extra_vars:
      operation: "validate_shared_infrastructure"
    on_success: [2]
    on_failure: [end]
  
  - node_id: 2
    name: "Provision Shared Infrastructure"
    type: job_template
    job_template: "Run ML Platform Playbook"
    extra_vars:
      operation: "provision_shared_infrastructure"
      # Survey variables passed automatically
    credentials: ["Azure Service Principal"]
    on_success: [3]
    on_failure: [end]
  
  - node_id: 3
    name: "Notify Platform Admin"
    type: notification
    notifications: ["Email - Platform Admin", "Slack - Platform Channel"]
    message: |
      ML platform shared infrastructure provisioned successfully.
      
      Resource Group: {{ azure_ml_platform_shared_rg }}
      Region: {{ azure_region }}
      Key Vault: {{ azure_ml_platform_keyvault }}
      Container Registry: {{ azure_ml_platform_acr }}
      
      Teams can now request workspaces via the self-service catalog.
```

---

#### Workflow 2: Provision Team Workspace

**Workflow Nodes:**

```yaml
workflow_nodes:
  - node_id: 1
    name: "Validate Workspace Request"
    type: job_template
    job_template: "Validate Workspace Request"
    extra_vars:
      team_name: "{{ azure_ml_team_name }}"
      requested_budget: "{{ azure_ml_team_budget_limit }}"
      vm_size: "{{ azure_ml_team_compute_vm_size }}"
      max_nodes: "{{ azure_ml_team_compute_max_nodes }}"
    on_success: [2]
    on_failure: [end]
    # Validates: shared infra exists, workspace name unique, budget calculation
  
  - node_id: 2
    name: "Approval Gate (Budget > $5000 or GPU)"
    type: approval
    timeout: 3600  # 1 hour
    conditions:
      - "{{ azure_ml_team_budget_limit | int > 5000 or 'NC' in azure_ml_team_compute_vm_size }}"
    approvers: ["ML Platform Admins", "Finance Managers"]
    message: |
      Team {{ azure_ml_team_name }} requests ML workspace:
      
      Budget: ${{ azure_ml_team_budget_limit }}/month
      Compute: {{ azure_ml_team_compute_vm_size }} x {{ azure_ml_team_compute_max_nodes }} nodes
      Estimated monthly cost: ${{ estimated_monthly_cost }}
      
      Approve to proceed with provisioning.
    on_success: [3]
    on_failure: [7]  # Rejection notification
  
  - node_id: 3
    name: "Provision Team Workspace"
    type: job_template
    job_template: "Run ML Platform Playbook"
    extra_vars:
      operation: "provision_team_workspace"
      # Survey variables passed automatically
    credentials: ["Azure Service Principal"]
    on_success: [4]
    on_failure: [8]  # Failure cleanup
  
  - node_id: 4
    name: "Configure Budget Alerts"
    type: job_template
    job_template: "Configure Budget Alerts"
    extra_vars:
      team_name: "{{ azure_ml_team_name }}"
      budget_limit: "{{ azure_ml_team_budget_limit }}"
      contact_email: "{{ azure_ml_team_contact_email }}"
    on_success: [5]
    on_failure: [5]  # Continue even if alerts fail (non-critical)
  
  - node_id: 5
    name: "Generate RBAC Instructions"
    type: job_template
    job_template: "Generate RBAC Documentation"
    extra_vars:
      workspace_name: "{{ azure_ml_team_name }}-ml-workspace"
      resource_group: "{{ azure_resource_group }}"
    on_success: [6]
  
  - node_id: 6
    name: "Notify Team - Workspace Ready"
    type: notification
    notifications: ["Email - Requester", "Slack - Team Channel"]
    message: |
      Your ML workspace is ready!
      
      Workspace Name: {{ azure_ml_team_name }}-ml-workspace
      Region: {{ azure_region }}
      Budget: ${{ azure_ml_team_budget_limit }}/month
      
      Next Steps:
      1. Platform admin will grant your team access within 24 hours
      2. Access workspace: https://ml.azure.com
      3. View onboarding guide: https://wiki.company.com/ml-platform-onboarding
      
      Budget alerts will be sent to: {{ azure_ml_team_contact_email }}
      
      Questions? Contact ml-platform-support@company.com
  
  - node_id: 7
    name: "Notify Team - Request Rejected"
    type: notification
    notifications: ["Email - Requester"]
    message: |
      Your ML workspace request was not approved.
      
      Team: {{ azure_ml_team_name }}
      Requested Budget: ${{ azure_ml_team_budget_limit }}/month
      
      Please contact your manager or ml-platform-support@company.com for details.
  
  - node_id: 8
    name: "Cleanup Failed Provisioning"
    type: job_template
    job_template: "Cleanup Failed Workspace"
    extra_vars:
      team_name: "{{ azure_ml_team_name }}"
      operation: "cleanup_failed"
```

---

## Playbook Implementation

### Playbook Structure

**File:** `playbooks/self_service_ml_platform.yml`

**Operations:**
- `operation: provision_shared_infrastructure` — Create hub resources
- `operation: provision_team_workspace` — Create spoke resources
- `operation: delete_team_workspace` — Remove team workspace
- `operation: delete_shared_infrastructure` — Remove hub resources

**Vars File:** `playbooks/vars/self_service_ml_platform_vars.yml`

### Key Implementation Details

#### Idempotency
- Check if resource exists before creating using `*_info` modules
- For shared infrastructure: skip if exists, update tags only
- For team workspace: fail if workspace name collision detected
- All `azure_rm_resource` calls use `idempotency: true`

#### Error Handling
- Pre-flight validation checks quota, unique names, shared infra existence
- Budget validation: `max_nodes * vm_hourly_rate * 730 < budget_limit`
- On failure: tag partial resources with `provisioning_failed: true` for cleanup
- Generate detailed error report with remediation steps

#### Security
- No credential logging (`no_log: true` on sensitive tasks)
- Storage account uses managed identity (no account keys in playbook vars)
- Key Vault uses RBAC (no access policies)
- Service principal needs: Contributor + User Access Administrator (for RBAC assignment)

---

## Error Handling & Validation

### Pre-Flight Validation

#### Before Provisioning Shared Infrastructure

**Checks:**
- Azure subscription quota: Key Vault (max 500), ACR, App Insights
- Resource providers registered: `Microsoft.KeyVault`, `Microsoft.ContainerRegistry`, `Microsoft.Insights`, `Microsoft.MachineLearningServices`
- Globally unique names available: Key Vault (DNS check `<name>.vault.azure.net`), ACR (DNS check `<name>.azurecr.io`)
- Service principal permissions: Contributor role on subscription scope

**Implementation:**
```yaml
- name: Validate Azure resource providers
  azure.azcollection.azure_rm_resourceprovider:
    namespace: "{{ item }}"
    state: registered
  loop:
    - Microsoft.KeyVault
    - Microsoft.ContainerRegistry
    - Microsoft.Insights
    - Microsoft.MachineLearningServices
  register: _provider_check
  failed_when: _provider_check is failed

- name: Check Key Vault name availability
  azure.azcollection.azure_rm_resource:
    resource_group: "{{ azure_ml_platform_shared_rg }}"
    provider: Microsoft.KeyVault
    resource_type: checkNameAvailability
    api_version: "2023-07-01"
    method: POST
    body:
      name: "{{ azure_ml_platform_keyvault }}"
      type: "Microsoft.KeyVault/vaults"
  register: _kv_check
  failed_when: not _kv_check.response.nameAvailable
```

#### Before Provisioning Team Workspace

**Checks:**
- Shared infrastructure exists (Key Vault, ACR, App Insights)
- Workspace name doesn't already exist
- Budget calculation: `estimated_monthly_cost < budget_limit`
- Storage account name globally unique
- VM size quota available in region

**Budget Validation Logic:**
```python
# Estimated monthly cost calculation
vm_hourly_rate = {
    'Standard_DS3_v2': 0.27,
    'Standard_DS4_v2': 0.54,
    'Standard_NC6s_v3': 3.06,
    'Standard_NC12s_v3': 6.12
}

estimated_monthly_cost = (
    max_nodes * vm_hourly_rate[vm_size] * 730 +  # Compute
    storage_gb * 0.02 +  # Storage (estimate 100GB)
    50  # Workspace overhead (App Insights, etc.)
)

if estimated_monthly_cost > budget_limit:
    fail("Estimated cost $%.2f exceeds budget $%d. Reduce max_nodes or choose smaller VM size." 
         % (estimated_monthly_cost, budget_limit))
```

### Failure Recovery

#### Shared Infrastructure Failures

| Failure | Root Cause | Recovery Action |
|---------|-----------|-----------------|
| Key Vault creation fails | Name conflict or quota | Suggest alternative name with random suffix |
| ACR creation fails | Quota exceeded | Suggest smaller SKU (Basic) or different region |
| App Insights fails | Rare permission issue | Mark non-critical, allow playbook to continue with warning |

#### Team Workspace Failures

| Failure | Root Cause | Recovery Action |
|---------|-----------|-----------------|
| Workspace creation fails | Quota exhausted | Provide quota increase link, tag resources for cleanup |
| Storage account fails | Name conflict | Auto-retry with `-<4-digit-random>` suffix |
| Compute cluster fails | VM size quota | Suggest smaller VM size, provide quota request link |
| RBAC assignment fails | Missing User Access Administrator | Document manual RBAC steps, proceed with provisioning |

**Cleanup on Failure:**
```yaml
- name: Tag failed resources for cleanup
  azure.azcollection.azure_rm_resource:
    resource_group: "{{ azure_resource_group }}"
    provider: "{{ item.provider }}"
    resource_type: "{{ item.type }}"
    resource_name: "{{ item.name }}"
    api_version: "{{ item.api_version }}"
    state: present
    body:
      tags:
        provisioning_status: "failed"
        provisioning_error: "{{ ansible_failed_result.msg | default('unknown') }}"
        cleanup_candidate: "true"
  when: workspace_provisioning_failed
  loop: "{{ created_resources }}"

- name: Generate failure report
  ansible.builtin.template:
    src: failure_report.md.j2
    dest: "/tmp/{{ azure_ml_team_name }}-failure-report.md"
  vars:
    error_message: "{{ ansible_failed_result.msg }}"
    remediation_steps: "{{ remediation_lookup[failure_type] }}"
```

---

## Testing Strategy

### Unit Testing

**Playbook Validation:**
```bash
# Syntax check
ansible-playbook --syntax-check playbooks/self_service_ml_platform.yml

# Linting
ansible-lint playbooks/self_service_ml_platform.yml

# Variable validation
ansible-playbook playbooks/self_service_ml_platform.yml --check \
  -e operation=provision_shared_infrastructure \
  -e azure_ml_platform_shared_rg=test-rg
```

### Integration Testing

**Test Scenario 1: Fresh Platform Setup**

```yaml
test_steps:
  - name: "Provision shared infrastructure"
    operation: provision_shared_infrastructure
    vars:
      azure_ml_platform_shared_rg: "ml-platform-test"
      azure_region: "eastus"
      azure_ml_platform_keyvault: "ml-test-kv-001"
      azure_ml_platform_acr: "mltestacr001"
    validate:
      - Key Vault exists and uses RBAC
      - ACR exists with admin user disabled
      - App Insights exists
      - All resources in same region
  
  - name: "Provision Team A workspace"
    operation: provision_team_workspace
    vars:
      azure_ml_team_name: "team-a"
      azure_ml_team_budget_limit: 2500
      azure_ml_team_compute_vm_size: "Standard_DS3_v2"
      azure_ml_team_compute_max_nodes: 4
    validate:
      - Workspace exists with managed identity
      - Storage account exists with lifecycle policy
      - Compute cluster: min=0, max=4, VM size correct
      - Datastore registered with managed identity auth
      - Base environment registered
      - All resources tagged with team: team-a
      - Workspace managed identity has AcrPull on ACR
      - Workspace managed identity has Storage Blob Data Contributor on storage
```

**Test Scenario 2: Multi-Team Isolation**

```yaml
test_steps:
  - name: "Provision Team B workspace"
    operation: provision_team_workspace
    vars:
      azure_ml_team_name: "team-b"
      azure_ml_team_budget_limit: 5000
      azure_ml_team_compute_vm_size: "Standard_DS4_v2"
      azure_ml_team_compute_max_nodes: 8
    validate:
      - Team B workspace isolated from Team A
      - Team B cannot access Team A storage
      - Both teams can pull from shared ACR
      - Shared App Insights receives telemetry from both
```

**Test Scenario 3: Cleanup**

```yaml
test_steps:
  - name: "Delete Team A workspace"
    operation: delete_team_workspace
    vars:
      azure_ml_team_name: "team-a"
    validate:
      - Team A workspace deleted
      - Team A storage account deleted
      - Shared infrastructure untouched
      - Team B workspace still functional
  
  - name: "Delete shared infrastructure"
    operation: delete_shared_infrastructure
    validate:
      - Key Vault deleted (soft-delete, 90-day recovery)
      - ACR deleted
      - App Insights deleted
      - Resource group deleted
```

### Validation Checklist

**Cost Controls:**
- [ ] Budget alert action group created with correct emails
- [ ] Alert rules fire at 50%, 80%, 100% thresholds
- [ ] All resources tagged with `team: <name>`
- [ ] Compute cluster has `min_instances: 0`
- [ ] Estimated monthly cost calculated and validated against budget

**Security:**
- [ ] Key Vault uses RBAC (`enable_rbac_authorization: true`)
- [ ] Storage uses managed identity (no account keys in playbook output)
- [ ] Workspace managed identity has least-privilege roles
- [ ] No passwords or secrets logged (check playbook output)
- [ ] Service principal permissions validated in pre-flight check

**Functionality:**
- [ ] Workspace accessible in Azure ML Studio (`https://ml.azure.com`)
- [ ] Compute cluster can scale up from 0 to max nodes
- [ ] Datastore registered and accessible from workspace
- [ ] Base environment can run simple training job (`print('hello')`)
- [ ] Storage account lifecycle policy applies after 90 days

---

## Documentation Deliverables

### 1. Playbook Documentation

**File:** `playbooks/SELF_SERVICE_ML_PLATFORM.md`

**Sections:**
1. **Overview** — Architecture diagram, business value, user stories
2. **Prerequisites** — Azure subscription, quota, service principal permissions, AAP version
3. **Variables Reference** — Complete variable list with descriptions, defaults, validation rules
4. **Usage Examples** — Command-line examples for both operations
5. **AAP Integration** — Survey specs, workflow templates, approval gates
6. **Multi-Team Patterns** — Provisioning multiple teams, RBAC configuration, isolation verification
7. **Cost Management** — Budget alerts setup, tagging strategy, chargeback report generation
8. **Security Best Practices** — Private endpoints, network isolation, Key Vault secret management
9. **Troubleshooting** — Common errors, remediation steps, support escalation

**Format:** Follow existing pattern from `playbooks/MLOPS_LIFECYCLE.md`

---

### 2. AAP Survey Specifications

**Directory:** `docs/aap_surveys/`

**Files:**
- `platform_setup_survey.json` — JSON export of shared infrastructure survey
- `request_workspace_survey.json` — JSON export of team workspace survey
- `workflow_templates.md` — Step-by-step guide to configure workflows in AAP UI
- `rbac_configuration.md` — Guide for manually assigning team members to workspaces post-provisioning

---

### 3. User Onboarding Guide

**File:** `docs/ml_platform_onboarding.md`

**Target Audience:** Data scientists requesting their first workspace

**Sections:**
1. **Requesting a Workspace** — Step-by-step survey walkthrough with screenshots
2. **Approval Process** — What to expect, timeline, escalation if rejected
3. **Accessing Your Workspace** — Login to Azure ML Studio, workspace navigation
4. **Uploading Data** — Create datastore, register dataset, access from training job
5. **Submitting Training Jobs** — Use base environment, customize environment, monitor job
6. **Cost Monitoring** — View budget alerts, check current spend, optimize compute usage
7. **Getting Help** — Slack channel, email support, troubleshooting FAQ

---

### 4. Platform Admin Guide

**File:** `docs/platform_admin_guide.md`

**Target Audience:** Platform administrators managing the ML platform

**Sections:**
1. **Initial Setup** — Run shared infrastructure survey, validate deployment
2. **Team Workspace Provisioning** — Approve requests, validate provisioning, assign RBAC
3. **Cost Management** — Monitor budgets, generate chargeback reports, adjust limits
4. **Security Hardening** — Enable private endpoints, configure network isolation, rotate credentials
5. **Maintenance** — Update base environments, patch vulnerabilities, resize shared resources
6. **Troubleshooting** — Common provisioning errors, quota management, failed workspace cleanup

---

## Success Criteria

### Functional Requirements

- [ ] Shared infrastructure provisioned in < 5 minutes
- [ ] Team workspace provisioned in < 10 minutes
- [ ] Multiple teams can be provisioned without naming conflicts or resource conflicts
- [ ] Budget alerts trigger correctly at 50%, 80%, 100% thresholds
- [ ] Compute auto-scales to zero after 5 minutes idle
- [ ] All resources tagged with `team` for cost allocation
- [ ] Workspace managed identity can pull from shared ACR
- [ ] Workspace managed identity can read secrets from shared Key Vault

### Documentation Requirements

- [ ] Playbook documentation follows existing `MLOPS_LIFECYCLE.md` pattern
- [ ] AAP survey specs complete and tested in AAP UI
- [ ] Workflow templates documented with node-by-node breakdown
- [ ] User onboarding guide covers end-to-end self-service flow
- [ ] Troubleshooting section has remediation steps for common errors
- [ ] Architecture diagrams included (ASCII art for quick reference, optionally PNG for formal docs)

### Quality Requirements

- [ ] Passes `ansible-lint` with no errors
- [ ] Idempotent: running provisioning twice produces same result (no duplicate resources)
- [ ] All failures provide actionable error messages with remediation steps
- [ ] No secrets logged to console or files (verified with `no_log` on sensitive tasks)
- [ ] Follows existing collection patterns: naming conventions, variable structure, role usage
- [ ] Integration tests pass for all scenarios (fresh setup, multi-team, cleanup)

---

## Implementation Phases

### Phase 1: Core Playbook (1-2 days)
- [ ] Create `playbooks/self_service_ml_platform.yml` with both operations
- [ ] Create `playbooks/vars/self_service_ml_platform_vars.yml` with all variables
- [ ] Implement shared infrastructure provisioning
- [ ] Implement team workspace provisioning
- [ ] Add deletion operations for both

### Phase 2: Cost Controls (1 day)
- [ ] Add budget alert action group creation
- [ ] Add budget alert rules at 50%, 80%, 100%
- [ ] Implement cost allocation tagging on all resources
- [ ] Add budget validation logic (estimated cost vs. limit)

### Phase 3: Error Handling (1 day)
- [ ] Add pre-flight validation checks
- [ ] Implement failure recovery logic
- [ ] Add cleanup tasks for failed provisioning
- [ ] Generate detailed error reports

### Phase 4: Documentation (2 days)
- [ ] Write `playbooks/SELF_SERVICE_ML_PLATFORM.md`
- [ ] Create AAP survey JSON exports
- [ ] Write workflow template configuration guide
- [ ] Write user onboarding guide
- [ ] Write platform admin guide

### Phase 5: Testing & Validation (1 day)
- [ ] Run integration tests (fresh setup, multi-team, cleanup)
- [ ] Validate cost controls (budget alerts, tagging)
- [ ] Validate security (RBAC, managed identity, no credential logging)
- [ ] Fix any issues found during testing

**Total Estimated Effort:** 6-7 days

---

## Future Enhancements

### Short-Term (Next Quarter)
- **Private Endpoints** — Network isolation for workspaces, storage, Key Vault
- **Workspace Auto-Pause** — Azure Automation to pause workspaces after hours
- **Custom Environment Library** — Pre-built environments for PyTorch, TensorFlow, Spark
- **Cost Showback Dashboard** — Power BI dashboard for monthly cost reports per team

### Medium-Term (Next 6 Months)
- **Azure Policy Integration** — Enforce required tags, allowed regions, allowed VM sizes
- **AAP RBAC Automation** — Use Graph API to auto-assign workspace roles based on AD groups
- **Shared Dataset Catalog** — Centralized data registry for cross-team data sharing
- **MLOps Template Integration** — Link workspace provisioning to MLOps lifecycle playbook

### Long-Term (Next Year)
- **Multi-Cloud Support** — Extend to AWS SageMaker, GCP Vertex AI
- **GitOps Integration** — Workspace-as-code with GitLab/GitHub repo per team
- **FinOps Automation** — Auto-shutdown, rightsizing recommendations, spot instance support
- **Compliance Automation** — SOC2, HIPAA, ISO 27001 control validation per workspace

---

## Appendix

### A. Variable Reference

**Shared Infrastructure Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `operation` | string | Yes | `create` | `provision_shared_infrastructure`, `provision_team_workspace`, `delete_team_workspace`, `delete_shared_infrastructure` |
| `azure_ml_platform_shared_rg` | string | Yes | `ml-platform-shared` | Resource group for shared infrastructure |
| `azure_region` | string | Yes | `eastus` | Azure region for all resources |
| `azure_ml_platform_keyvault` | string | Yes | None | Key Vault name (globally unique, 3-24 chars) |
| `azure_ml_platform_acr` | string | Yes | None | Container Registry name (globally unique, 5-50 alphanumeric) |
| `azure_ml_platform_appinsights` | string | Yes | `ml-platform-insights` | Application Insights name |
| `azure_ml_platform_admin_email` | string | Yes | None | Platform admin email for alerts |

**Team Workspace Variables:**

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_team_name` | string | Yes | None | Team name (lowercase, 3-20 alphanumeric/hyphens) |
| `azure_ml_team_contact_email` | string | Yes | None | Team contact email for budget alerts |
| `azure_ml_team_budget_limit` | integer | Yes | `2500` | Monthly budget limit in USD |
| `azure_ml_team_compute_vm_size` | string | Yes | `Standard_DS3_v2` | VM size for compute cluster |
| `azure_ml_team_compute_max_nodes` | integer | Yes | `4` | Maximum nodes in compute cluster |
| `azure_ml_team_data_access_scope` | string | No | `restricted` | `restricted`, `shared`, `external` |

### B. Azure Resource Naming Conventions

| Resource Type | Pattern | Example | Notes |
|---------------|---------|---------|-------|
| Resource Group | `<name>-<env>` | `ml-platform-shared` | Shared infrastructure |
| Resource Group | `<team>-ml-rg` | `team-a-ml-rg` | Team workspace RG (optional, can share) |
| ML Workspace | `<team>-ml-workspace` | `team-a-ml-workspace` | Max 260 chars |
| Storage Account | `<team>mlstor` | `teamamlstor` | Max 24 chars, alphanumeric only |
| Key Vault | `<name>-kv-<nnn>` | `ml-platform-kv-001` | Max 24 chars, globally unique |
| Container Registry | `<name>acr<nnn>` | `mlplatformacr001` | Max 50 chars, alphanumeric only, globally unique |
| Compute Cluster | `<team>-compute` | `team-a-compute` | Max 260 chars |
| Datastore | `<team>_datastore` | `team_a_datastore` | Underscores allowed |
| Environment | `<team>-base-env` | `team-a-base-env` | Max 260 chars |

### C. Cost Estimation Examples

**Example 1: Small Team ($2,500/month)**
- Compute: Standard_DS3_v2, max 4 nodes
- Usage: 20% utilization (146 hours/month average)
- Storage: 100GB blob storage
- **Monthly Cost:** ~$158 (well under budget)

**Example 2: Standard Team ($5,000/month)**
- Compute: Standard_DS4_v2, max 8 nodes
- Usage: 40% utilization (584 hours/month average)
- Storage: 500GB blob storage
- **Monthly Cost:** ~$1,261 (comfortable buffer)

**Example 3: GPU Team ($10,000/month)**
- Compute: Standard_NC6s_v3 (1x V100), max 4 nodes
- Usage: 50% utilization (730 hours/month average)
- Storage: 1TB blob storage
- **Monthly Cost:** ~$4,474 (leaves room for burst usage)

### D. Security Checklist

**Least-Privilege RBAC:**
- [ ] Workspace managed identity has only required roles (AcrPull, Key Vault Secrets User, Storage Blob Data Contributor)
- [ ] Service principal has Contributor (not Owner) on subscription
- [ ] Team members have AzureML Data Scientist (not Contributor) on workspace
- [ ] Viewers have Reader (read-only) on workspace

**Credential Management:**
- [ ] No storage account keys logged or stored in variables
- [ ] Managed identity used for all resource access
- [ ] Key Vault stores external API keys (not in playbook vars)
- [ ] Service principal client secret stored in AAP credential vault

**Network Security (Future Enhancement):**
- [ ] Private endpoints for workspace, storage, Key Vault
- [ ] Disable public network access on workspace
- [ ] Managed virtual network for workspace (allow_only_approved_outbound)
- [ ] NSG rules restrict access to approved IP ranges

### E. Troubleshooting Guide

**Error: Key Vault name already exists**
```
Resolution: Key Vault names are globally unique. Try:
1. Check if name is taken: nslookup <name>.vault.azure.net
2. Add random suffix: ml-platform-kv-<random-4-digits>
3. Use different naming pattern: <company>-ml-kv-<region>
```

**Error: Workspace provisioning quota exceeded**
```
Resolution: 
1. Check current quota: az ml workspace list --query "length([])"
2. Request increase: https://portal.azure.com -> Help + Support -> New support request
3. Use different region with available quota
4. Delete unused workspaces to free quota
```

**Error: Compute cluster creation fails (VM quota)**
```
Resolution:
1. Check quota: az vm list-usage --location eastus --query "[?name.value=='standardDSv2Family']"
2. Choose smaller VM size: Standard_DS2_v2 instead of Standard_DS3_v2
3. Request quota increase for DSv2 family
```

**Error: Budget alert not firing**
```
Resolution:
1. Verify action group email delivered (check spam folder)
2. Check budget scope matches resource group
3. Budget API can take 24 hours to activate
4. Verify alert threshold calculation: 50% of $5000 = $2500
```

---

## Approval

**Design Reviewed By:** [User]  
**Date:** 2026-09-01  
**Status:** Approved for Implementation  

**Next Step:** Invoke `writing-plans` skill to create implementation plan.
