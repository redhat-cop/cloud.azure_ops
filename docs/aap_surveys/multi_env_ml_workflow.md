# AAP Multi-Environment ML Deployment Workflow

This guide provides workflow template configuration for orchestrating multi-environment ML deployments with gated model promotion through Ansible Automation Platform.

## Prerequisites

- AAP 2.4+ with Automation Controller
- Azure Service Principal credential configured in AAP
- `cloud.azure_ops` collection installed on execution environment
- Project synced with this repository

## Workflow Architecture

The multi-environment ML deployment workflow implements a hub-and-spoke infrastructure with gated promotions from dev through staging to production:

```
┌─────────────────────────────────────────────────────────────────────┐
│                AAP Workflow: Multi-Environment ML Deployment         │
│                                                                     │
│  ┌─────────────────┐                                                │
│  │ Provision Hub   │                                                │
│  │ (One-time)      │                                                │
│  └────────┬────────┘                                                │
│           │                                                         │
│           ▼                                                         │
│  ┌────────────────────────────────────────┐                         │
│  │   Provision Environments (Parallel)    │                         │
│  │  ┌─────┐  ┌──────────┐  ┌──────────┐  │                         │
│  │  │ Dev │  │ Staging  │  │   Prod   │  │                         │
│  │  └─────┘  └──────────┘  └──────────┘  │                         │
│  └────────────────┬───────────────────────┘                         │
│                   │                                                 │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ Register Model in Dev Workspace │                                │
│  └────────────────┬────────────────┘                                │
│                   │                                                 │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ Automated Gate: Accuracy Check  │                                │
│  │ (min_accuracy ≥ 0.90)           │                                │
│  └────────────────┬────────────────┘                                │
│                   │ [PASS]                                          │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ 🔐 Manual Approval Node         │                                │
│  │ (Staging Promotion)             │                                │
│  └────────────────┬────────────────┘                                │
│                   │ [APPROVED]                                      │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ Promote Model to Staging        │                                │
│  │ (promotion_approved=true)       │                                │
│  └────────────────┬────────────────┘                                │
│                   │                                                 │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ Automated Gate: Accuracy Check  │                                │
│  │ (min_accuracy ≥ 0.90)           │                                │
│  └────────────────┬────────────────┘                                │
│                   │ [PASS]                                          │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ 🔐 Manual Approval Node         │                                │
│  │ (Prod Promotion)                │                                │
│  └────────────────┬────────────────┘                                │
│                   │ [APPROVED]                                      │
│                   ▼                                                 │
│  ┌─────────────────────────────────┐                                │
│  │ Promote Model to Prod           │                                │
│  │ (promotion_approved=true)       │                                │
│  └─────────────────────────────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflow Components

### Job Templates

The workflow requires the following job templates:

#### 1. Provision Shared Infrastructure

**Job Template Configuration:**
- **Name:** `Multi-Env ML - Provision Hub`
- **Job Type:** Run
- **Inventory:** localhost
- **Project:** [Your project]
- **Playbook:** `playbooks/multi_env_ml_deployment.yml`
- **Credentials:** Azure Service Principal
- **Extra Variables:**
  ```yaml
  menv_operation: provision_shared_infrastructure
  ```
- **Options:** Skip tags, verbosity, and prompt configurations
- **Note:** The playbook uses `menv_operation` as the operation selector. Omit it (or set `menv_operation: all`) to run the full lifecycle demo.

#### 2. Provision Environment (Reusable)

**Job Template Configuration:**
- **Name:** `Multi-Env ML - Provision Environment`
- **Job Type:** Run
- **Inventory:** localhost
- **Project:** [Your project]
- **Playbook:** `playbooks/multi_env_ml_deployment.yml`
- **Credentials:** Azure Service Principal
- **Extra Variables:**
  ```yaml
  menv_operation: provision_environment
  ```
- **Options:** Enable "Prompt on launch" for Extra Variables (to set `azure_ml_menv_environment`)

#### 3. Register Model in Dev

**Job Template Configuration:**
- **Name:** `Multi-Env ML - Register Dev Model`
- **Job Type:** Run
- **Inventory:** localhost
- **Project:** [Your project]
- **Playbook:** Custom playbook or inline command module calling `azure.azcollection.azure_rm_ml_model`
- **Credentials:** Azure Service Principal
- **Note:** The full playbook includes this step inline. For workflow-based invocation, extract to a standalone job template.

#### 4. Promote Model

**Job Template Configuration:**
- **Name:** `Multi-Env ML - Promote Model`
- **Job Type:** Run
- **Inventory:** localhost
- **Project:** [Your project]
- **Playbook:** `playbooks/multi_env_ml_deployment.yml`
- **Credentials:** Azure Service Principal
- **Extra Variables:**
  ```yaml
  menv_operation: promote_model
  ```
- **Options:** Enable "Prompt on launch" for Extra Variables (to set `azure_ml_menv_promote_source`, `azure_ml_menv_promote_target`, and `azure_ml_menv_promotion_approved`)
- **Note:** AAP approval nodes preceding the promote jobs set `azure_ml_menv_promotion_approved: true`. The promote jobs also require `azure_ml_menv_promote_source` and `azure_ml_menv_promote_target` to specify the promotion path (e.g., `dev` → `staging`).

## Workflow Template Configuration

### Step 1: Create Workflow Template

1. Navigate to **Resources → Templates → Add → Workflow Template**
2. Configure:
   - **Name:** `Multi-Env ML - Full Deployment Pipeline`
   - **Organization:** [Your organization]
   - **Inventory:** localhost
   - **Options:** Enable "Enable Webhook"

### Step 2: Build Workflow Visualizer Graph

Click **Visualizer** and add the following nodes in sequence:

#### Node 1: Provision Hub
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Provision Hub`
- **Convergence:** All

#### Node 2a: Provision Dev
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Provision Environment`
- **Extra Variables:** `azure_ml_menv_environment: dev`
- **Parent:** Node 1 (on success)

#### Node 2b: Provision Staging (Parallel)
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Provision Environment`
- **Extra Variables:** `azure_ml_menv_environment: staging`
- **Parent:** Node 1 (on success)

#### Node 2c: Provision Prod (Parallel)
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Provision Environment`
- **Extra Variables:** `azure_ml_menv_environment: prod`
- **Parent:** Node 1 (on success)

#### Node 3: Register Dev Model
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Register Dev Model`
- **Convergence:** All (wait for Node 2a, 2b, 2c)
- **Parent:** Node 2a, 2b, 2c (on success)

#### Node 4: Approval - Staging Promotion
- **Type:** Approval
- **Name:** "Approve Staging Promotion"
- **Timeout:** 3600 seconds (1 hour)
- **Parent:** Node 3 (on success)
- **Note:** The automated accuracy gate runs inside the promote job; this approval node gates entry to the promotion

#### Node 5: Promote to Staging
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Promote Model`
- **Extra Variables:**
  ```yaml
  azure_ml_menv_promote_source: dev
  azure_ml_menv_promote_target: staging
  azure_ml_menv_promotion_approved: true
  ```
- **Parent:** Node 4 (on success)

#### Node 6: Approval - Prod Promotion
- **Type:** Approval
- **Name:** "Approve Prod Promotion"
- **Timeout:** 3600 seconds (1 hour)
- **Parent:** Node 5 (on success)

#### Node 7: Promote to Prod
- **Type:** Job Template
- **Job Template:** `Multi-Env ML - Promote Model`
- **Extra Variables:**
  ```yaml
  azure_ml_menv_promote_source: staging
  azure_ml_menv_promote_target: prod
  azure_ml_menv_promotion_approved: true
  ```
- **Parent:** Node 6 (on success)

### Step 3: Create Survey for Workflow

1. In the workflow template, click **Survey** tab → **Add**
2. Add the following survey fields:

#### Survey Field 1: Resource Group
- **Question:** Azure Resource Group
- **Answer Variable Name:** `azure_resource_group`
- **Answer Type:** Text
- **Required:** Yes
- **Default:** `ml-platform-multienv`

#### Survey Field 2: Azure Region
- **Question:** Azure Region
- **Answer Variable Name:** `azure_region`
- **Answer Type:** Multiple Choice (single select)
- **Multiple Choice Options:**
  ```
  eastus
  westus2
  westeurope
  centralus
  ```
- **Required:** Yes
- **Default:** `eastus`

#### Survey Field 3: Minimum Accuracy Threshold
- **Question:** Minimum Model Accuracy (0.0 - 1.0)
- **Answer Variable Name:** `azure_ml_menv_min_accuracy`
- **Answer Type:** Float
- **Min:** 0.0
- **Max:** 1.0
- **Required:** Yes
- **Default:** `0.90`

#### Survey Field 4: Model Name
- **Question:** Model Name
- **Answer Variable Name:** `azure_ml_menv_model_name`
- **Answer Type:** Text
- **Required:** Yes
- **Default:** `menv-model`

#### Survey Field 5: Model Version
- **Question:** Model Version
- **Answer Variable Name:** `azure_ml_menv_model_version`
- **Answer Type:** Text
- **Required:** Yes
- **Default:** `1`

#### Survey Field 6: Promotion Approved
- **Question:** Promotion Approved (set by approval workflow node)
- **Answer Variable Name:** `azure_ml_menv_promotion_approved`
- **Answer Type:** Multiple Choice (single select)
- **Multiple Choice Options:**
  ```
  true
  false
  ```
- **Required:** Yes
- **Default:** `false`

### Step 4: Test Workflow

1. Launch the workflow template
2. Fill out the survey with test values
3. Monitor the workflow visualizer:
   - Hub provisioning completes
   - Three environment provisioning jobs run in parallel
   - Dev model registration completes
   - Approval node pauses for staging promotion approval
   - Upon approval, promote job runs (dev → staging); automated gate checks accuracy, then model is promoted
   - Approval node pauses for prod promotion approval
   - Upon approval, promote job runs (staging → prod); automated gate checks accuracy, then model is promoted
4. Verify infrastructure in Azure portal
5. Check audit trail in blob storage container `audit/`

## Survey JSON Export

For programmatic survey creation, use the following JSON structure:

```json
{
  "name": "Multi-Environment ML Deployment Survey",
  "description": "Configure hub-and-spoke ML deployment with gated promotions",
  "spec": [
    {
      "question_name": "Azure Resource Group",
      "question_description": "Resource group for all ML infrastructure (hub and spokes)",
      "required": true,
      "type": "text",
      "variable": "azure_resource_group",
      "min": 1,
      "max": 90,
      "default": "ml-platform-multienv"
    },
    {
      "question_name": "Azure Region",
      "question_description": "Azure location for all resources",
      "required": true,
      "type": "multiplechoice",
      "variable": "azure_region",
      "choices": ["eastus", "westus2", "westeurope", "centralus"],
      "default": "eastus"
    },
    {
      "question_name": "Minimum Model Accuracy",
      "question_description": "Accuracy threshold (0.0-1.0) for automated promotion gate",
      "required": true,
      "type": "float",
      "variable": "azure_ml_menv_min_accuracy",
      "min": 0.0,
      "max": 1.0,
      "default": 0.90
    },
    {
      "question_name": "Model Name",
      "question_description": "Name of the ML model to promote across environments",
      "required": true,
      "type": "text",
      "variable": "azure_ml_menv_model_name",
      "min": 1,
      "max": 255,
      "default": "menv-model"
    },
    {
      "question_name": "Model Version",
      "question_description": "Model version identifier",
      "required": true,
      "type": "text",
      "variable": "azure_ml_menv_model_version",
      "min": 1,
      "max": 255,
      "default": "1"
    },
    {
      "question_name": "Promotion Approved",
      "question_description": "Manual approval gate (set by approval workflow node)",
      "required": true,
      "type": "multiplechoice",
      "variable": "azure_ml_menv_promotion_approved",
      "choices": ["true", "false"],
      "default": "false"
    }
  ]
}
```

## Approval Workflow Patterns

### Pattern 1: Pre-Promotion Approval (Recommended)

Place the approval node **before** the promotion job and conditionally set `azure_ml_menv_promotion_approved=true`:

```
[Register Model] → [Approval Node] → [Promote to Staging (approved=true)]
```

In the promotion job's extra variables, reference the workflow variable set by the approval:

```yaml
azure_ml_menv_promotion_approved: true
```

### Pattern 2: Post-Promotion Approval (Audit Gate)

Place the approval node **after** the promotion job for audit purposes (promotion already happened, approval serves as a checkpoint before next stage):

```
[Promote to Staging] → [Approval Node] → [Next Stage]
```

This pattern is less common but useful when promotions are automatically triggered by CI/CD and require post-hoc review.

## Webhook Integration

To trigger the workflow from external CI/CD systems:

1. In the workflow template, enable **Enable Webhook**
2. Generate webhook key
3. Copy webhook URL: `https://<aap-controller>/api/v2/workflow_job_templates/<id>/github/`
4. Configure webhook in GitHub, GitLab, or Azure DevOps:
   - **Payload URL:** [Webhook URL from step 3]
   - **Content type:** `application/json`
   - **Events:** Push to `main` branch, Pull Request merge

Example webhook payload:

```json
{
  "extra_vars": {
    "azure_resource_group": "ml-platform-multienv",
    "azure_region": "eastus",
    "azure_ml_menv_min_accuracy": 0.95,
    "azure_ml_menv_model_name": "fraud-detection-v2",
    "azure_ml_menv_model_version": "2"
  }
}
```

## RBAC Configuration

After workspace provisioning, assign team members to workspace roles:

```bash
# Get workspace resource ID
WORKSPACE_ID=$(az ml workspace show \
  --resource-group ml-platform-multienv \
  --name ml-platform-multienv-ml-prod \
  --query id -o tsv)

# Assign AzureML Data Scientist role
az role assignment create \
  --assignee user@company.com \
  --role "AzureML Data Scientist" \
  --scope $WORKSPACE_ID
```

See `playbooks/MULTI_ENV_ML_DEPLOYMENT.md` for complete security and RBAC guidance.

## Troubleshooting

* **Workflow stuck at approval node**: Check AAP Approval UI. Ensure approvers are configured in the approval node settings.
* **Promotion job fails with "approval gate failed"**: The approval node must set `azure_ml_menv_promotion_approved=true`. Verify extra variables are passed correctly from the approval node to the promotion job.
* **Accuracy gate fails**: Review model `accuracy` tag in the source workspace. Ensure training jobs set this tag. Lower `azure_ml_menv_min_accuracy` in the survey if testing with dummy models.
* **Parallel environment provisioning jobs fail**: Check VM quota in the target region. Ensure sufficient quota for 3 concurrent workspace deployments.
* **Audit records missing**: Verify the audit storage account and container were provisioned by the hub job. Check service principal has `Storage Blob Data Contributor` role on the audit storage account.
