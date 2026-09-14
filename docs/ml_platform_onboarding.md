# ML Platform User Onboarding Guide

Welcome to the self-service ML platform! This guide will help you request and access your team's ML workspace.

## Step 1: Request a Workspace

1. Navigate to AAP self-service catalog: `https://aap.company.com/catalog`
2. Find **"Request ML Workspace"** in the catalog
3. Click **Launch**
4. Fill out the survey:
   - **Team Name:** Choose a unique, descriptive name (lowercase, hyphens, 3-20 chars)
     - Good: `datascience-alpha`, `ml-research-team`
     - Bad: `Team 1`, `ds_alpha`, `DataScienceAlpha`
   - **Team Contact Email:** Email for budget alerts
   - **Monthly Budget:** Select based on expected usage
     - $1,000: Development/testing
     - $2,500: Small team (2-3 people)
     - $5,000: Standard team (4-8 people)
     - $10,000: Large team (requires approval)
   - **Compute VM Size:** Choose based on workload
     - `Standard_DS3_v2`: CPU workloads (4 cores, 14GB RAM) - $0.27/hr
     - `Standard_DS4_v2`: Larger CPU workloads (8 cores, 28GB RAM) - $0.54/hr
     - `Standard_NC6s_v3`: GPU workloads (1x V100) - $3.06/hr (requires approval)
   - **Maximum Nodes:** How many compute nodes can run simultaneously
   - **Data Access:** Select `restricted` (team data only) for most cases

5. Click **Next** → **Launch**

## Step 2: Approval Process

- Requests under $5,000 with CPU compute: **Automatic provisioning** (~10 minutes)
- Requests over $5,000 or GPU compute: **Requires approval** (1-4 hours)
  - Approval notification sent to your manager and platform admin
  - You'll receive email when approved or rejected

## Step 3: Access Your Workspace

Once provisioned (you'll receive email notification):

1. Navigate to Azure ML Studio: `https://ml.azure.com`
2. Sign in with your company credentials
3. Select your workspace from the dropdown (named `<team-name>-ml-workspace`)
4. Wait for platform admin to grant you access (24-48 hours)
   - You'll receive `AzureML Data Scientist` role
   - Check email for access confirmation

## Step 4: Upload Your First Dataset

1. In Azure ML Studio, navigate to **Data → Datastores**
2. Your team has a pre-configured datastore: `<team-name>_datastore`
3. Click **Browse** → **Upload files** or **Upload folder**
4. Upload your training data

5. Register as a data asset:
   - Navigate to **Data → Data assets → Create**
   - Name: `my-dataset-v1`
   - Type: File or Folder
   - Datastore: `<team-name>_datastore`
   - Path: Select uploaded files

## Step 5: Submit Your First Training Job

1. Navigate to **Notebooks**
2. Create a new notebook or upload existing `.ipynb` file
3. Select compute: `<team-name>-compute`
4. Run your training script

**Example:**

```python
from azureml.core import Workspace, Dataset, Experiment, ScriptRunConfig

# Connect to workspace
ws = Workspace.from_config()

# Load dataset
dataset = Dataset.get_by_name(ws, name='my-dataset-v1')

# Configure training job
config = ScriptRunConfig(
    source_directory='./src',
    script='train.py',
    arguments=['--data', dataset.as_named_input('training_data')],
    compute_target='<team-name>-compute',
    environment='<team-name>-base-env'
)

# Submit
experiment = Experiment(ws, 'my-experiment')
run = experiment.submit(config)
run.wait_for_completion(show_output=True)
```

## Cost Monitoring

### Budget Alerts

You'll receive email alerts when your team's spending reaches:
- **50% of budget** → Warning, monitor usage
- **80% of budget** → Critical, reduce usage or request increase
- **100% of budget** → Over budget, contact platform admin

### Viewing Current Spend

1. Azure Portal: `https://portal.azure.com`
2. Navigate to **Cost Management + Billing → Cost analysis**
3. Filter by tag: `team = <your-team-name>`
4. View current month spending

### Cost Optimization Tips

- **Use scale-to-zero compute:** Cluster automatically scales to 0 nodes after 5 minutes idle
- **Choose smallest VM size** that meets your needs (start with DS3_v2, upgrade if needed)
- **Delete old experiments** and models you no longer need
- **Use spot instances** for non-critical workloads (coming soon)

## Getting Help

- **Platform documentation:** `https://wiki.company.com/ml-platform`
- **Slack channel:** `#ml-platform-support`
- **Email support:** `ml-platform-support@company.com`
- **Office hours:** Tuesdays 2-3pm, Thursdays 10-11am

## FAQ

**Q: Can I request multiple workspaces for my team?**
A: Generally one workspace per team. If you need separate dev/prod environments, contact platform admin.

**Q: How do I add/remove team members?**
A: Contact platform admin via `#ml-platform-support` with list of emails and desired role (Data Scientist, Compute Operator, Reader).

**Q: My compute cluster is stuck "Provisioning"?**
A: This usually means VM quota exhausted. Contact platform admin to request quota increase.

**Q: Can I use my own Docker images?**
A: Yes! Push to shared ACR (`mlplatformacr001`) and reference in environment definition. Your workspace identity has `AcrPull` permissions.

**Q: How do I share datasets with another team?**
A: Request `shared` data access scope during workspace provisioning, then contact platform admin for cross-team permissions.
