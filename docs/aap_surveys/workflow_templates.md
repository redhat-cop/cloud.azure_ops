# AAP Workflow Templates Configuration Guide

This guide provides step-by-step instructions for configuring AAP workflow templates for the self-service ML platform.

## Prerequisites

- AAP 2.4+ with Automation Controller
- Azure Service Principal credential configured in AAP
- `cloud.azure_ops` collection installed on execution environment
- Project synced with this repository

## Workflow 1: Provision Shared Infrastructure

**Purpose:** One-time setup of shared ML platform resources (admin-only)

### Step 1: Create Job Template

1. Navigate to **Resources → Templates → Add → Job Template**
2. Configure:
   - **Name:** `ML Platform - Provision Shared Infrastructure`
   - **Job Type:** Run
   - **Inventory:** localhost
   - **Project:** [Your project]
   - **Playbook:** `playbooks/self_service_ml_platform.yml`
   - **Credentials:** Azure Service Principal
   - **Extra Variables:**
     ```yaml
     operation: provision_shared_infrastructure
     ```
   - **Options:** Enable "Prompt on launch" for Extra Variables

### Step 2: Create Survey

1. In the job template, click **Survey** tab → **Add**
2. Import survey JSON from `docs/aap_surveys/platform_setup_survey.json`
3. Save survey

### Step 3: Test

1. Launch template
2. Fill survey with test values
3. Verify shared infrastructure created in Azure

---

## Workflow 2: Provision Team Workspace

**Purpose:** Self-service team workspace provisioning (repeatable)

### Step 1: Create Job Template

1. Navigate to **Resources → Templates → Add → Job Template**
2. Configure:
   - **Name:** `ML Platform - Provision Team Workspace`
   - **Job Type:** Run
   - **Inventory:** localhost
   - **Project:** [Your project]
   - **Playbook:** `playbooks/self_service_ml_platform.yml`
   - **Credentials:** Azure Service Principal
   - **Extra Variables:**
     ```yaml
     operation: provision_team_workspace
     azure_ml_platform_shared_rg: ml-platform-shared
     azure_ml_platform_admin_email: admin@company.com
     ```
   - **Options:** Enable "Prompt on launch" for Extra Variables

### Step 2: Create Survey

1. In the job template, click **Survey** tab → **Add**
2. Import survey JSON from `docs/aap_surveys/request_workspace_survey.json`
3. Save survey

### Step 3: Create Workflow Template (Optional - with Approval)

1. Navigate to **Resources → Templates → Add → Workflow Template**
2. **Name:** `ML Platform - Request Workspace (with Approval)`
3. Click **Visualizer**
4. Add nodes:
   - **Node 1:** Approval Node
     - Name: "Approve Workspace Request"
     - Timeout: 3600 seconds
     - Approvers: [ML Platform Admins group]
   - **Node 2:** Job Template: `ML Platform - Provision Team Workspace`
     - On success of Node 1
5. Save workflow

### Step 4: Test

1. Launch workflow
2. Fill survey
3. Approve in AAP approval UI
4. Verify workspace created

---

## RBAC Configuration

After workspace provisioning, platform admin must manually assign team members:

```bash
# Get workspace details
az ml workspace show \
  --resource-group ml-platform-shared \
  --name team-alpha-ml-workspace

# Assign team member to workspace
az role assignment create \
  --assignee user@company.com \
  --role "AzureML Data Scientist" \
  --scope /subscriptions/<subscription-id>/resourceGroups/ml-platform-shared/providers/Microsoft.MachineLearningServices/workspaces/team-alpha-ml-workspace
```

See `playbooks/SELF_SERVICE_ML_PLATFORM.md` for complete RBAC guide.
