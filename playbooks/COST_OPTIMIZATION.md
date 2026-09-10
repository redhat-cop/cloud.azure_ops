## cloud.azure_ops.cost_optimization playbook

A playbook to automate Azure ML/AI cost optimization through intelligent compute lifecycle management, event-driven controls, and continuous right-sizing.

This reference architecture demonstrates how Ansible Automation Platform (AAP) reduces Azure ML infrastructure costs by 30-50% through scheduled automation, event-driven overrides, and metrics-driven right-sizing decisions. The solution combines cost governance with operational flexibility.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AAP (Orchestration Layer)                         │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────────┐ │
│  │ Scheduled Jobs │  │ EDA Rulebooks  │  │ Approval Gate         │ │
│  │ (cron)         │  │ (event-driven) │  │ (optional)            │ │
│  └───────┬────────┘  └───────┬────────┘  └───────┬───────────────┘ │
└──────────┼───────────────────┼───────────────────┼─────────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               ▼
           ┌────────────────────────────────────────┐
           │  cost_optimization.yml playbook        │
           │  (thin wrapper, calls role)            │
           └────────────────┬───────────────────────┘
                            ▼
           ┌────────────────────────────────────────┐
           │  azure_ml_cost_optimization role       │
           │                                        │
           │  Operations:                           │
           │  • shutdown_compute                    │
           │  • startup_compute                     │
           │  • analyze_and_rightsize               │
           │  • manage_ptu                          │
           │  • generate_roi_report                 │
           └────────────────┬───────────────────────┘
                            ▼
    ┌──────────────┬────────────────┬──────────────┐
    ▼              ▼                ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────┐
│ Azure   │  │ Azure ML │  │ Azure OpenAI │  │ Azure   │
│ Monitor │  │ Compute  │  │ PTU          │  │ Cost    │
│ (metrics)│ │ Clusters │  │              │  │ Mgmt API│
└─────────┘  └──────────┘  └──────────────┘  └─────────┘
```

#### Cost Optimization Patterns

| Pattern | Trigger | Action | Savings |
|---------|---------|--------|---------|
| Scheduled Lifecycle | 6pm/8am cron | Shutdown/startup of idle compute | 12-16 hrs/day × clusters |
| Event-Driven Override | Cost threshold breach | Emergency shutdown (EDA rulebook) | $5K-$20K per incident |
| Continuous Right-Sizing | Weekly schedule | Auto-downsize underutilized clusters | 10-20% compute cost reduction |
| PTU Optimization | Weekly schedule | Scale OpenAI PTU based on utilization | 20-50% if over-provisioned |
| ROI Tracking | Monthly (1st of month) | Generate cost savings report | Visibility into ROI |

---

### Prerequisites

**Required:**
- Ansible >= 2.14.0
- `azure.azcollection` >= 2.0.0 (install via `ansible-galaxy collection install azure.azcollection`)
- Azure Service Principal with roles:
  - `Contributor` (to manage compute)
  - `Monitoring Reader` (to query metrics)
  - `Cost Management Reader` (to access cost data)
- Azure CLI configured with appropriate credentials
- Access to target Azure subscription and resource group

**Optional:**
- Azure Event Grid + Service Bus (for EDA integration)
- Ansible Automation Platform (for scheduling and workflow templates)
- Event-Driven Ansible (EDA) controller (for event-driven triggers)

**Tested Environments:**
- Azure ML workspace in East US / West US / West Europe
- Azure OpenAI accounts with Provisioned Throughput Units (PTU)
- Compute clusters: Standard_DS series, Standard_NC series (GPU)

---

### Playbook Structure

```yaml
# playbooks/cost_optimization.yml
---
- name: Azure ML/AI cost optimization
  hosts: localhost
  gather_facts: true
  
  vars_files:
    - vars/cost_optimization_vars.yml
  
  tasks:
    - Validate required variables
    - Include role: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        operation: "{{ operation }}"
```

**Key Design Decisions:**

1. **Thin Wrapper Pattern** — The playbook delegates all logic to the `azure_ml_cost_optimization` role. This keeps the playbook simple while allowing role reuse in other playbooks.

2. **Operation Dispatch** — The `operation` variable (set via `-e operation=X` or in AAP) determines which task file in the role executes. Valid operations: `shutdown_compute`, `startup_compute`, `analyze_and_rightsize`, `manage_ptu`, `generate_roi_report`.

3. **Required Variables** — The playbook validates three mandatory variables before delegating to the role:
   - `operation` — The operation to perform
   - `azure_resource_group` — Target Azure ML resource group
   - `azure_region` — Azure region (e.g., eastus, westus2)

4. **Facts Gathering** — Enabled by default to provide system facts (e.g., `ansible_date_time` for timestamped logs).

---

### Variables Reference

#### Core Configuration

```yaml
# Mandatory variables (set via -e or in AAP)
operation: "shutdown_compute"  # Required: shutdown_compute | startup_compute | analyze_and_rightsize | manage_ptu | generate_roi_report
azure_resource_group: "ml-platform-prod"  # Required: Resource group containing ML workspaces
azure_region: "eastus"  # Required: Azure region

# Optional scope filters (empty = all resources in resource group)
azure_ml_cost_optimization_workspaces: []  # Restrict to specific workspace names
azure_ml_cost_optimization_compute_targets: []  # Restrict to specific compute cluster names
azure_ml_cost_optimization_openai_accounts: []  # Restrict to specific OpenAI accounts
```

#### Shutdown/Startup Configuration

```yaml
# Shutdown behavior
azure_ml_cost_optimization_preserve_running_jobs: true  # If true, skip clusters with active jobs

# Preserve running jobs: Prevents disruption to long-running training jobs by
# skipping clusters that have active (Running/Preparing) jobs.
```

**Example: Emergency Shutdown (EDA)**
```yaml
-e azure_ml_cost_optimization_preserve_running_jobs=false \
-e azure_ml_cost_optimization_emergency_mode=true
```

#### Right-Sizing Configuration

```yaml
# CPU utilization threshold (%)
azure_ml_cost_optimization_rightsize_cpu_threshold: 30
# Downsize if average CPU < this for entire analysis window

# Analysis window (days)
azure_ml_cost_optimization_rightsize_analysis_days: 7
# Require 7 consecutive days of low usage before downsizing

# Allowed VM sizes for auto-resize
azure_ml_cost_optimization_rightsize_allowed_sizes:
  - Standard_DS3_v2
  - Standard_DS4_v2
  - Standard_DS5_v2

# Minimum allowed size (safety guardrail)
azure_ml_cost_optimization_rightsize_min_size: "Standard_DS3_v2"
# Never downsize below this size (prevents accidental downsizing to underpowered VMs)
```

**Right-Sizing Logic:**
1. Query Azure Monitor metrics (past 7 days, 1-hour granularity)
2. Calculate average CPU % across entire window
3. If avg CPU < 30%, identify next smaller VM size
4. Check: New size is in `rightsize_allowed_sizes` and not below `rightsize_min_size`
5. Apply resize via Azure API
6. Return summary with estimated savings

**Example: Conservative Right-Sizing**
```yaml
-e azure_ml_cost_optimization_rightsize_cpu_threshold=20 \
-e azure_ml_cost_optimization_rightsize_analysis_days=14 \
-e azure_ml_cost_optimization_rightsize_allowed_sizes='["Standard_DS4_v2","Standard_DS5_v2"]'
```

#### PTU Management Configuration

```yaml
# Target PTU utilization (%)
azure_ml_cost_optimization_ptu_target_utilization: 80
# Scale up if utilization > this (within provisioned PTU limits)

# Scale-down threshold (%)
azure_ml_cost_optimization_ptu_scale_down_threshold: 50
# Scale down PTU if utilization < this for 7 consecutive days

# Example: Azure OpenAI with 100 PTU ($5,000/month)
# If utilization < 50% for 7 days, downscale to 50 PTU ($2,500/month)
```

**PTU Optimization Safety:**
- Never scale above current PTU capacity
- Never scale below 1 PTU
- Requires 7 consecutive days of consistent utilization before scaling
- Logs utilization trends for analysis

#### EDA Override Configuration

```yaml
# Emergency mode (set by EDA rulebook on cost threshold breach)
azure_ml_cost_optimization_emergency_mode: false
# Recorded on audit entries to flag budget-triggered runs

# Budget alert action
azure_ml_cost_optimization_budget_alert_action: "shutdown_non_critical"
# Valid values:
#   - shutdown_all: Stop all clusters immediately
#   - shutdown_non_critical: Stop only clusters not tagged critical=true
#   - alert_only: Send notification, no action

# Example: EDA triggered emergency shutdown
# emergency_mode: true
# budget_alert_action: "shutdown_non_critical"  # Preserve critical workloads
```

**EDA Integration:**
EDA rulebooks can override scheduled behavior when cost thresholds are breached:

```yaml
# EDA rulebook example
rules:
  - name: Budget threshold exceeded
    condition: event.data.costThreshold >= 80
    action:
      run_job_template:
        name: "Cost Optimization - Emergency Shutdown"
        extra_vars:
          operation: "shutdown_compute"
          emergency_mode: true
          budget_alert_action: "shutdown_non_critical"
          azure_resource_group: "{{ event.data.resourceGroup }}"
```

#### ROI Tracking Configuration

```yaml
# Baseline monthly cost (USD) before automation
azure_ml_cost_optimization_roi_baseline_monthly_cost: 0  # MUST UPDATE THIS
# Recommended: Run `az costmanagement query` to measure average of past 3 months
# This baseline is used to calculate ROI and savings percentage

# Tracking start date (ISO 8601)
azure_ml_cost_optimization_roi_tracking_start_date: ""  # MUST UPDATE THIS
# Format: "2026-06-01" (date automation was enabled)
# Used to track cost reduction from baseline date forward

# Report output path
azure_ml_cost_optimization_roi_report_path: "/tmp/roi_report_{{ ansible_date_time.date }}.md"
# Generated monthly with savings analysis
```

**Baseline Calculation Steps:**

```bash
# Step 1: Query Azure Cost Management API for past 3 months
az costmanagement query \
  --type ActualCost \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --timeframe Custom \
  --time-period from="2026-03-01" to="2026-05-31" \
  --scope "/subscriptions/{subscription-id}"

# Step 2: Calculate average
baseline_monthly_cost = (march_cost + april_cost + may_cost) / 3

# Step 3: Set variable
azure_ml_cost_optimization_roi_baseline_monthly_cost: 15000  # USD
azure_ml_cost_optimization_roi_tracking_start_date: "2026-06-01"  # Automation enabled
```

#### Audit Logging Configuration

```yaml
# Enable audit log output
azure_ml_cost_optimization_enable_audit_log: false
# If true, writes operation log to file

# Audit log path
azure_ml_cost_optimization_audit_log_path: "/tmp/azure_ml_cost_optimization_{{ ansible_date_time.date }}.yml"

# Example audit log entry:
_audit_log:
  - timestamp: "2026-09-09T18:05:32Z"
    operation: "shutdown_compute"
    cluster: "ds-team-a-compute"
    workspace: "team-a-ml-workspace"
    action: "shutdown"
    previous_state: "running"
    new_state: "stopped"
    reason: "scheduled_shutdown"
    triggered_by: "AAP User: admin"
```

---

### Usage Examples

#### Example 1: Scheduled Daily Shutdown (6pm)

```bash
# Run via AAP Job Template or manual execution
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=shutdown_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_preserve_running_jobs=true
```

**Expected Output:**
```
TASK [Run cost optimization operation]
ok: [localhost] => changed=true
  msg: |
    Shutdown complete:
    - Clusters stopped: 7
    - Clusters skipped: 2 (active jobs)
    - Total cost savings: $21.42/hour ($15,625/month at 14hr/day)
```

#### Example 2: Scheduled Daily Startup (8am)

```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=startup_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus
```

**Expected Output:**
```
TASK [Run cost optimization operation]
ok: [localhost] => changed=true
  msg: |
    Startup complete:
    - Clusters started: 7
    - Clusters already running: 2
    - Total clusters available: 9
```

#### Example 3: Weekly Right-Sizing Analysis (Sunday 2am)

```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=analyze_and_rightsize \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_rightsize_analysis_days=7 \
  -e azure_ml_cost_optimization_rightsize_cpu_threshold=30
```

**Expected Output:**
```
TASK [Run cost optimization operation]
ok: [localhost] => changed=true
  msg: |
    Right-sizing analysis complete:
    - Clusters analyzed: 9
    - Clusters resized: 3
      - ds-team-a (DS5_v2 → DS4_v2): $131/month saved
      - ds-team-b (DS5_v2 → DS4_v2): $131/month saved
      - ds-team-c (DS4_v2 → DS3_v2): $87/month saved
    - Total monthly savings: $349
    - Total annual savings: $4,188
```

#### Example 4: Manual Right-Sizing for Specific Clusters

```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=analyze_and_rightsize \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e 'azure_ml_cost_optimization_compute_targets=["ds-team-a-compute","ds-team-b-compute"]'
```

#### Example 5: PTU Optimization for Azure OpenAI

```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=manage_ptu \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_ptu_target_utilization=80 \
  -e azure_ml_cost_optimization_ptu_scale_down_threshold=50
```

**Expected Output:**
```
TASK [Run cost optimization operation]
ok: [localhost] => changed=true
  msg: |
    PTU optimization complete:
    - Accounts analyzed: 2
    - Accounts optimized: 1
      - account-a: 100 PTU → 50 PTU ($2,500/month saved)
    - Total monthly savings: $2,500
    - Total annual savings: $30,000
```

#### Example 6: Monthly ROI Report Generation

```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=generate_roi_report \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_roi_baseline_monthly_cost=15000 \
  -e azure_ml_cost_optimization_roi_tracking_start_date=2026-06-01
```

**Output File:** `/tmp/roi_report_2026-09-09.md` (contains full cost analysis)

#### Example 7: Emergency Shutdown (EDA Triggered)

```bash
# Run when EDA detects cost threshold breach
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=shutdown_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_preserve_running_jobs=false \
  -e azure_ml_cost_optimization_emergency_mode=true \
  -e azure_ml_cost_optimization_budget_alert_action=shutdown_non_critical
```

#### Example 8: Check Mode Validation (Dry-Run)

```bash
# Validate without making changes
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=shutdown_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  --check
```

---

### Ansible Automation Platform Integration

#### Workflow Template: Cost Optimization Orchestration

**Purpose:** Coordinate all cost optimization operations via AAP interface

**Template Configuration:**

```yaml
# AAP Workflow Template: "ML Cost Optimization - Master"

Workflow Nodes:
  1. Conditional: Check current time
     ├─ If 6pm weekday → Run "Shutdown Daily"
     ├─ If 8am weekday → Run "Startup Daily"
     └─ If Sunday 2am → Run "Right-Sizing Weekly"

Job Templates:
  - "Cost Optimization - Shutdown Daily"
    playbook: cloud.azure_ops.cost_optimization
    extra_vars:
      operation: shutdown_compute
      azure_ml_cost_optimization_preserve_running_jobs: true
    credentials: Azure Service Principal
    limit: localhost
    
  - "Cost Optimization - Startup Daily"
    playbook: cloud.azure_ops.cost_optimization
    extra_vars:
      operation: startup_compute
    credentials: Azure Service Principal
    limit: localhost
    
  - "Cost Optimization - Right-Sizing Weekly"
    playbook: cloud.azure_ops.cost_optimization
    extra_vars:
      operation: analyze_and_rightsize
      azure_ml_cost_optimization_rightsize_analysis_days: 7
    credentials: Azure Service Principal
    limit: localhost
    
  - "Cost Optimization - PTU Optimization"
    playbook: cloud.azure_ops.cost_optimization
    extra_vars:
      operation: manage_ptu
    credentials: Azure Service Principal
    limit: localhost
    
  - "Cost Optimization - ROI Report"
    playbook: cloud.azure_ops.cost_optimization
    extra_vars:
      operation: generate_roi_report
    credentials: Azure Service Principal
    limit: localhost
```

#### Scheduled Execution

**Daily Shutdown (6pm weekdays):**
```yaml
Schedule: "Cost Opt - Shutdown 6pm"
  - Unified Job Template: "Cost Optimization - Shutdown Daily"
  - Recurrence: Every weekday at 6:00pm (UTC)
  - Timezone: America/New_York
```

**Daily Startup (8am weekdays):**
```yaml
Schedule: "Cost Opt - Startup 8am"
  - Unified Job Template: "Cost Optimization - Startup Daily"
  - Recurrence: Every weekday at 8:00am (UTC)
  - Timezone: America/New_York
```

**Weekly Right-Sizing (Sunday 2am):**
```yaml
Schedule: "Cost Opt - Right-Sizing Sunday 2am"
  - Unified Job Template: "Cost Optimization - Right-Sizing Weekly"
  - Recurrence: Every Sunday at 2:00am (UTC)
  - Timezone: America/New_York
```

**Monthly ROI Report (1st of month, 8am):**
```yaml
Schedule: "Cost Opt - ROI Report Monthly"
  - Unified Job Template: "Cost Optimization - ROI Report"
  - Recurrence: On day 1 of every month at 8:00am (UTC)
  - Timezone: America/New_York
```

#### Survey Configuration for Manual Execution

```yaml
# AAP Job Template: "Cost Optimization - Manual Execution"
playbook: cloud.azure_ops.cost_optimization

survey:
  - variable: operation
    question: "Which operation to run?"
    type: multiple_choice
    choices:
      - shutdown_compute
      - startup_compute
      - analyze_and_rightsize
      - manage_ptu
      - generate_roi_report
    required: true
    default: shutdown_compute
  
  - variable: azure_resource_group
    question: "Resource group to operate on?"
    type: text
    required: true
    default: ml-platform-prod
  
  - variable: azure_region
    question: "Azure region?"
    type: text
    required: true
    default: eastus
  
  - variable: azure_ml_cost_optimization_preserve_running_jobs
    question: "Preserve running jobs? (shutdown_compute only)"
    type: boolean
    default: true
    condition:
      - variable: operation
        value: shutdown_compute
  
  - variable: azure_ml_cost_optimization_rightsize_analysis_days
    question: "Analysis window (days, for right-sizing)?"
    type: integer
    default: 7
    condition:
      - variable: operation
        value: analyze_and_rightsize
  
  - variable: azure_ml_cost_optimization_rightsize_cpu_threshold
    question: "CPU threshold % (for right-sizing)?"
    type: integer
    default: 30
    condition:
      - variable: operation
        value: analyze_and_rightsize
  
  - variable: azure_ml_cost_optimization_roi_baseline_monthly_cost
    question: "Baseline monthly cost (USD, for ROI report)?"
    type: integer
    default: 15000
    condition:
      - variable: operation
        value: generate_roi_report
```

#### Approval Gates

**Scenario: Right-Sizing Requires Approval**

```yaml
Workflow Template: "Cost Optimization - With Approval"

Nodes:
  1. Job: Right-Sizing Analysis
  2. Approval: "Proceed with downsizing?"
     - Timeout: 2 hours
     - Approved by: Finance team
  3. Job: Apply Right-Sizing (conditional on approval)
```

---

### Event-Driven Ansible Integration

#### EDA Rulebook for Cost Alerts

**File:** `eda_cost_alerts.yml` (reference, not included in collection)

```yaml
---
- name: Azure Cost Management event-driven automation
  hosts: all
  sources:
    - ansible.eda.azure_service_bus:
        connection_str: "{{ azure_service_bus_connection }}"
        queue_name: "cost-management-events"
  
  rules:
    - name: Budget threshold 80% exceeded - emergency shutdown
      condition: event.data.costThreshold >= 80
      action:
        run_job_template:
          name: "Cost Optimization - Emergency Shutdown"
          organization: "Default"
          extra_vars:
            operation: "shutdown_compute"
            emergency_mode: true
            budget_alert_action: "shutdown_non_critical"
            azure_resource_group: "{{ event.data.resourceGroup }}"
    
    - name: Budget threshold 95% exceeded - full shutdown
      condition: event.data.costThreshold >= 95
      action:
        run_job_template:
          name: "Cost Optimization - Full Shutdown"
          organization: "Default"
          extra_vars:
            operation: "shutdown_compute"
            emergency_mode: true
            budget_alert_action: "shutdown_all"
            azure_resource_group: "{{ event.data.resourceGroup }}"
    
    - name: Cost anomaly detected - generate ROI report
      condition: event.data.costAnomaly == true
      action:
        run_job_template:
          name: "Cost Optimization - ROI Report"
          organization: "Default"
          extra_vars:
            operation: "generate_roi_report"
            alert_team: true
            azure_resource_group: "{{ event.data.resourceGroup }}"
    
    - name: Budget reset - restart compute
      condition: event.data.budgetReset == true
      action:
        run_job_template:
          name: "Cost Optimization - Startup"
          organization: "Default"
          extra_vars:
            operation: "startup_compute"
            azure_resource_group: "{{ event.data.resourceGroup }}"
```

#### Azure Event Grid Setup

**Prerequisites:**
1. Azure Cost Management budget created
2. Azure Service Bus namespace + queue
3. Event Grid system topic

**Setup Commands:**

```bash
# Create Event Grid system topic
az eventgrid system-topic create \
  --name cost-management-topic \
  --resource-group ml-platform-prod \
  --source /subscriptions/{subscription-id} \
  --topic-type Microsoft.CostManagement.Budgets

# Create Service Bus resources
az servicebus namespace create \
  --name ml-cost-events \
  --resource-group ml-platform-prod \
  --sku Standard

az servicebus queue create \
  --name cost-management-events \
  --namespace-name ml-cost-events \
  --resource-group ml-platform-prod

# Create event subscription
az eventgrid system-topic event-subscription create \
  --name cost-to-servicebus \
  --system-topic-name cost-management-topic \
  --resource-group ml-platform-prod \
  --endpoint-type servicebusqueue \
  --endpoint /subscriptions/{subscription-id}/resourceGroups/ml-platform-prod/providers/Microsoft.ServiceBus/namespaces/ml-cost-events/queues/cost-management-events

# Get Service Bus connection string (for EDA)
az servicebus namespace authorization-rule keys list \
  --name RootManageSharedAccessKey \
  --namespace-name ml-cost-events \
  --resource-group ml-platform-prod \
  --query primaryConnectionString -o tsv
```

#### EDA Controller Configuration

```yaml
# /etc/ansible/eda/controller_config.yml
EDA_SERVICE_BUS_CONNECTION: "Endpoint=sb://ml-cost-events.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=..."

# Run EDA controller
ansible-rulebook -i inventory.yml -r eda_cost_alerts.yml -v
```

#### Hybrid Trigger Flow

**Normal Operation (Scheduled):**
```
6pm daily → AAP Scheduled Job → Shutdown playbook → Shutdown idle compute
8am daily → AAP Scheduled Job → Startup playbook → Restore clusters
2am Sunday → AAP Scheduled Job → Right-sizing playbook → Analyze metrics
```

**Override Scenario (EDA):**
```
3pm (cost hits 80%) → Azure Event Grid event
  → Service Bus queue message
  → EDA rulebook receives event
  → Triggers AAP job: "Cost Optimization - Emergency Shutdown"
  → Playbook runs with emergency_mode=true
  → Shutdown non-critical clusters only (clusters tagged critical=true are preserved)
6pm (scheduled) → Shutdown playbook runs
  → No-op (clusters already stopped)
```

---

### ROI Framework

#### Cost Savings Methodology

**Three-Part Cost Reduction:**

1. **Scheduled Lifecycle Management** — Shutdown idle compute during non-business hours
   - GPU cluster: $3.06/hour × 14 hours/day × 5 days/week × 4.3 weeks = $921/month per cluster
   
2. **Right-Sizing** — Downsize underutilized clusters to smaller VM types
   - DS5_v2 ($0.72/hr) → DS4_v2 ($0.54/hr) = $131/month per cluster
   
3. **PTU Optimization** — Scale Azure OpenAI PTU based on actual utilization
   - 100 PTU ($5,000/month) → 50 PTU ($2,500/month) = $2,500/month per account

#### ROI Calculation Example: Medium Team (15 Data Scientists)

**Baseline (Pre-Automation):**
- 10 ML compute clusters: 6 × DS4_v2, 4 × NC6s_v3
- Azure OpenAI: 100 PTU ($5,000/month)
- Storage: ~$500/month
- Assumed utilization: 40% (60% idle waste)
- **Monthly Cost: $35,000**

**Cost Breakdown:**
- CPU clusters: 6 × 730 hrs × $0.54/hr = $2,365
- GPU clusters: 4 × 730 hrs × $3.06/hr = $8,935
- OpenAI PTU: $5,000
- Storage: $500
- Other: $18,200

**Post-Automation Actions:**

| Action | Method | Savings |
|--------|--------|---------|
| Scheduled shutdown | 6pm-8am + weekends = 507 hrs/month | 6 clusters × 507 × $0.54 = $1,643/month |
| GPU shutdown | Same schedule for 4 GPU clusters | 4 clusters × 507 × $3.06 = $6,206/month |
| Right-sizing | 3 clusters: DS5_v2 → DS4_v2 | 3 × $131 = $393/month |
| PTU optimization | Downscale to 50 PTU | $2,500/month |
| **Total Monthly Savings** | | **$10,742/month (31%)** |

**Post-Automation Monthly Cost: $24,258**

**Annual ROI:**
- Savings: $10,742 × 12 = **$128,904/year**
- AAP subscription: ~$10,000/year
- Implementation cost: ~$20,000 (one-time)
- **Net Year 1 ROI: $98,904** (4.9x return)
- **Ongoing ROI: 12.9x return/year**

#### Baseline Establishment Process

```bash
# Step 1: Query past 3 months costs
az costmanagement query \
  --type ActualCost \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping name="ResourceGroup" type="Dimension" \
  --timeframe Custom \
  --time-period from="2026-03-01" to="2026-05-31" \
  --scope "/subscriptions/{subscription-id}"

# Step 2: Calculate baseline
# March: $32,000
# April: $35,000
# May: $36,000
# Baseline = ($32k + $35k + $36k) / 3 = $34,333

# Step 3: Set playbook variable
azure_ml_cost_optimization_roi_baseline_monthly_cost: 34333
azure_ml_cost_optimization_roi_tracking_start_date: "2026-06-01"

# Step 4: Generate monthly reports (1st of month)
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=generate_roi_report \
  -e azure_resource_group=ml-platform-prod \
  -e azure_ml_cost_optimization_roi_baseline_monthly_cost=34333 \
  -e azure_ml_cost_optimization_roi_tracking_start_date=2026-06-01
```

#### Report Content

Generated monthly ROI reports include:

**Cost Metrics:**
- Baseline monthly cost (from variable)
- Current month-to-date cost (from Cost Management API)
- Savings amount and percentage
- Projected annual savings

**Action Metrics:**
- Number of shutdown events
- Number of startup events
- Number of clusters rightsized
- Number of PTU optimizations
- Number of EDA emergency triggers

**Cost Breakdown:**
- Compute costs by cluster
- Compute costs by workspace
- OpenAI costs by account
- Storage costs
- Other costs

**Trend Analysis:**
- Month-over-month cost comparison (past 6 months)
- Cost per data scientist (if team size tracked)
- Cost per ML job (if job metrics available)

---

### Troubleshooting Guide

#### Common Issues

**Issue: "Required variable {{ item }} not defined"**
- **Cause:** Missing required variable (operation, azure_resource_group, or azure_region)
- **Solution:** Provide variable via `-e` flag:
  ```bash
  ansible-playbook playbooks/cost_optimization.yml \
    -e operation=shutdown_compute \
    -e azure_resource_group=ml-platform-prod \
    -e azure_region=eastus
  ```

**Issue: "Insufficient permissions"**
- **Cause:** Service principal missing required roles
- **Solution:** Grant roles to service principal:
  ```bash
  # Get service principal object ID
  SERVICE_PRINCIPAL_ID=$(az ad sp show --id $AZURE_CLIENT_ID --query id -o tsv)
  
  # Grant Contributor role
  az role assignment create \
    --assignee $SERVICE_PRINCIPAL_ID \
    --role Contributor \
    --scope /subscriptions/{subscription-id}
  
  # Grant Monitoring Reader role
  az role assignment create \
    --assignee $SERVICE_PRINCIPAL_ID \
    --role "Monitoring Reader" \
    --scope /subscriptions/{subscription-id}
  
  # Grant Cost Management Reader role
  az role assignment create \
    --assignee $SERVICE_PRINCIPAL_ID \
    --role "Cost Management Reader" \
    --scope /subscriptions/{subscription-id}
  ```

**Issue: "Cluster not found"**
- **Cause:** Compute cluster deleted or name misspelled
- **Solution:** Verify cluster exists:
  ```bash
  az ml compute list --resource-group ml-platform-prod --workspace-name my-workspace
  ```

**Issue: "Active jobs running" (shutdown skipped)**
- **Cause:** `preserve_running_jobs=true` and jobs are running on cluster
- **Solution:** Either wait for jobs to complete or override:
  ```bash
  ansible-playbook playbooks/cost_optimization.yml \
    -e operation=shutdown_compute \
    -e azure_resource_group=ml-platform-prod \
    -e azure_ml_cost_optimization_preserve_running_jobs=false
  ```

**Issue: "Metrics API throttled"**
- **Cause:** Too many API calls to Azure Monitor
- **Solution:** Role includes exponential backoff retry logic (5s, 15s, 45s). If still failing:
  - Reduce number of clusters analyzed in single run
  - Increase `rightsize_analysis_days` to query fewer data points

**Issue: "Invalid VM size transition"**
- **Cause:** Attempted resize from GPU (NC) to CPU (DS) or unsupported size
- **Solution:** Ensure `rightsize_allowed_sizes` includes only valid sizes for each cluster type

**Issue: "Cost Management API unavailable"**
- **Cause:** Azure service outage or insufficient permissions
- **Solution:** Check permissions and retry after 30 minutes:
  ```bash
  # Verify Cost Management Reader role
  az role assignment list \
    --assignee $SERVICE_PRINCIPAL_ID \
    --query "[?roleDefinitionName=='Cost Management Reader']"
  ```

#### Check Mode Validation

```bash
# Validate playbook without making changes
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=shutdown_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  --check

# Expected output (no actual changes):
# TASK [Run cost optimization operation] ok: [localhost] => changed=false
# ... (lists what would happen)
```

#### Syntax Validation

```bash
# Validate playbook syntax
ansible-playbook --syntax-check playbooks/cost_optimization.yml
# Expected: "playbook: playbooks/cost_optimization.yml"

# Lint check
ansible-lint playbooks/cost_optimization.yml
# Expected: No errors (warnings acceptable)
```

#### Audit Log Analysis

```bash
# Enable audit logging
-e azure_ml_cost_optimization_enable_audit_log=true

# View generated audit log
cat /tmp/azure_ml_cost_optimization_2026-09-09.yml

# Extract failed operations
grep -A 10 "action: failed" /tmp/azure_ml_cost_optimization_2026-09-09.yml
```

#### Debug Logging

```bash
# Run with verbose output
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=shutdown_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -vvv  # -vvv for maximum verbosity
```

---

### Advanced Configurations

#### Multi-Workspace Right-Sizing

```bash
# Target specific workspaces
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=analyze_and_rightsize \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e 'azure_ml_cost_optimization_workspaces=["team-a-workspace","team-b-workspace"]'
```

#### Conservative Right-Sizing Policy

```bash
# Higher threshold, longer analysis window, restricted sizes
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=analyze_and_rightsize \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_rightsize_cpu_threshold=20 \
  -e azure_ml_cost_optimization_rightsize_analysis_days=14 \
  -e 'azure_ml_cost_optimization_rightsize_allowed_sizes=["Standard_DS4_v2","Standard_DS5_v2"]' \
  -e azure_ml_cost_optimization_rightsize_min_size="Standard_DS4_v2"
```

#### Aggressive Right-Sizing (Test Only)

```bash
# Lower threshold, shorter window (NOT recommended for production)
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=analyze_and_rightsize \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_rightsize_cpu_threshold=50 \
  -e azure_ml_cost_optimization_rightsize_analysis_days=3 \
  -e 'azure_ml_cost_optimization_rightsize_allowed_sizes=["Standard_DS1_v2","Standard_DS2_v2","Standard_DS3_v2","Standard_DS4_v2","Standard_DS5_v2"]'
```

#### Critical Workload Protection

```bash
# Tag clusters as critical=true, then use EDA with budget alert action
# In Azure ML clusters, add tags:
az ml compute update \
  --name ds-critical-compute \
  --resource-group ml-platform-prod \
  --workspace-name my-workspace \
  --set tags.critical=true

# EDA will skip clusters tagged critical=true during budget shutdown
```

---

### References

**Related Documentation:**
- `roles/azure_ml_cost_optimization/README.md` — Role implementation details
- `docs/superpowers/specs/2026-09-09-cost-optimization-design.md` — Full design specification
- `MLOPS_LIFECYCLE.md` — Related AAP workflow patterns

**Azure Documentation:**
- [Azure Cost Management API](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/api-tutorials)
- [Azure Machine Learning compute clusters](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-compute-cluster)
- [Azure Monitor metrics](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/metrics-supported)
- [Azure Event Grid + Service Bus integration](https://learn.microsoft.com/en-us/azure/event-grid/handler-service-bus)

**Ansible Automation Platform:**
- AAP Job Templates, Schedules, Workflow Templates
- AAP Inventory and Credentials
- AAP Approvals

**Event-Driven Ansible:**
- EDA rulebooks for event processing
- EDA sources (Azure Service Bus, Event Grid)
- EDA actions (run job templates, send notifications)

---

### Support and Feedback

For issues, enhancements, or feedback on this playbook:

1. **Check the troubleshooting section above**
2. **Review the design specification** (`docs/superpowers/specs/2026-09-09-cost-optimization-design.md`)
3. **Enable audit logging** (`-e azure_ml_cost_optimization_enable_audit_log=true`)
4. **Run syntax and lint checks** (`ansible-lint`, `ansible-playbook --syntax-check`)
5. **Test in check mode first** (`--check` flag)

---

## Summary

The `cost_optimization.yml` playbook provides a thin, idempotent wrapper around the `azure_ml_cost_optimization` role, enabling:

- **Scheduled cost control** — Shutdown/startup on business hour schedules
- **Event-driven overrides** — EDA triggers emergency shutdown on cost threshold breaches
- **Intelligent right-sizing** — Weekly metrics-driven cluster downsizing
- **PTU optimization** — Azure OpenAI cost reduction
- **ROI tracking** — Monthly savings reports with trend analysis

Integration with AAP provides scheduling, approvals, and survey-driven manual execution. EDA integration enables event-driven overrides when cost budgets are exceeded. The playbook follows Ansible best practices (idempotency, fact gathering, error handling) and includes comprehensive documentation and troubleshooting guidance.
