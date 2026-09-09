# Azure AI/ML Cost Optimization with AAP - Design Specification

**Jira:** ACA-5888  
**Date:** 2026-09-09  
**Status:** Design Approved  

## Executive Summary

This reference architecture demonstrates how Ansible Automation Platform (AAP) can reduce Azure ML infrastructure costs by 30-50% through intelligent resource lifecycle management. The solution combines scheduled automation, event-driven overrides, and continuous right-sizing to enforce cost governance without sacrificing data science productivity.

### Key Capabilities

- **Automated compute lifecycle** — Scheduled shutdown/startup of ML compute clusters and Azure OpenAI PTU based on business hours, saving 12-16 hours/day of idle time
- **Event-driven cost control** — EDA watches Azure Cost Management events and triggers emergency shutdown when budgets are exceeded
- **Intelligent right-sizing** — Weekly analysis of compute utilization with automated downsizing for underutilized clusters (CPU < 30% for 7 days)
- **PTU optimization** — Azure OpenAI Provisioned Throughput Unit management based on actual usage patterns
- **ROI tracking** — Automated monthly reports showing cost savings vs baseline, projected annual savings, and actions taken

### User Stories Addressed

1. **As a FinOps engineer**, I want automated compute shutdown schedules so that idle GPU clusters are not running overnight and on weekends
2. **As a platform engineer**, I want automated right-sizing recommendations applied via Ansible so that ML workspaces use appropriately sized compute
3. **As a CTO**, I want a cost optimization reference architecture so that I can justify AAP investment with concrete Azure ML savings projections

---

## Architecture

### High-Level Design

The platform implements three complementary cost optimization patterns:

```
┌─────────────────────────────────────────────────────────────┐
│  AAP (Orchestration Layer)                                  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │ Scheduled Jobs │  │ EDA Rulebooks  │  │ Approval Gate │ │
│  │ (cron)         │  │ (event-driven) │  │ (optional)    │ │
│  └───────┬────────┘  └───────┬────────┘  └───────┬───────┘ │
└──────────┼───────────────────┼───────────────────┼─────────┘
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

### Design Principles

1. **Hybrid triggering** — Default schedules provide predictable cost control; EDA overrides handle unexpected cost spikes
2. **Guardrails on automation** — Right-sizing only downsizes if utilization < 30% for 7 days; never auto-upsizes beyond configured max
3. **Idempotency** — Safe to run operations multiple times (e.g., shutdown already-stopped cluster is a no-op)
4. **Metrics-driven** — All decisions based on Azure Monitor/ML metrics, never guesswork
5. **No disruption** — Preserve running jobs (configurable), graceful shutdown modes, rollback capability

---

## Cost Optimization Patterns

### Pattern 1: Scheduled Lifecycle Management

**Purpose:** Shut down idle compute during non-business hours to eliminate wasted spend.

**Workflow:**
```
AAP Workflow Template (scheduled: daily 6pm weekdays)
  └─> cost_optimization.yml playbook
      └─> azure_ml_cost_optimization role (operation: shutdown_compute)
          └─> Shuts down idle Azure ML clusters + OpenAI PTU scale-down

AAP Workflow Template (scheduled: daily 8am weekdays)
  └─> cost_optimization.yml playbook
      └─> azure_ml_cost_optimization role (operation: startup_compute)
          └─> Starts clusters, restores to configured min_nodes
```

**Configuration:**
```yaml
# Shutdown at 6pm weekdays (graceful mode)
shutdown_mode: graceful  # Wait for running jobs to complete (max 30 min)
preserve_running_jobs: true  # Skip clusters with active jobs

# Startup at 8am weekdays
# Restores clusters to original min_nodes/max_nodes settings
```

**Cost Savings Example:**
- GPU cluster (Standard_NC6s_v3): $3.06/hour
- Idle time saved: 14 hours/day (6pm-8am) × 5 days = 70 hours/week
- Monthly savings: 70 × 4.3 weeks × $3.06 = **$921/cluster/month**

---

### Pattern 2: Event-Driven Override (EDA)

**Purpose:** React to unexpected cost spikes or budget thresholds with immediate action.

**Workflow:**
```
Azure Cost Management Event (budget threshold 80%)
  └─> Azure Event Grid → Service Bus Queue
      └─> EDA Rulebook watches Service Bus
          └─> Triggers cost_optimization.yml (operation: shutdown_compute)
              └─> Emergency shutdown (immediate mode, non-critical resources only)
```

**EDA Rulebook Example:**
```yaml
---
- name: Azure Cost Management event-driven automation
  hosts: all
  sources:
    - ansible.eda.azure_service_bus:
        connection_str: "{{ azure_service_bus_connection }}"
        queue_name: "cost-management-events"
  
  rules:
    - name: Budget threshold exceeded - emergency shutdown
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
```

**Override Behavior:**
- **3pm:** Budget hits 80% threshold → EDA triggers emergency shutdown
- **Emergency mode:** Immediate shutdown, skip graceful wait, shutdown non-critical clusters only
- **6pm:** Scheduled job runs → No-op (clusters already stopped)

**Cost Savings Example:**
- Budget overrun prevented: $5,000
- Non-critical clusters stopped 3 hours early: Additional $15 saved

---

### Pattern 3: Continuous Right-Sizing

**Purpose:** Automatically downsize underutilized clusters to match actual workload requirements.

**Workflow:**
```
AAP Workflow Template (scheduled: weekly Sunday 2am)
  └─> cost_optimization.yml playbook
      └─> azure_ml_cost_optimization role (operation: analyze_and_rightsize)
          └─> Queries 7-day metrics → downsizes underutilized clusters automatically
```

**Right-Sizing Logic:**
```
1. Collect Azure Monitor metrics (past 7 days, 1-hour granularity)
   - Metric: "Percentage CPU" (average)
2. Identify underutilized clusters:
   - Average CPU < 30% for entire 7-day window
3. Determine next smaller VM size:
   - Current: Standard_DS5_v2 ($0.72/hour)
   - Next smaller: Standard_DS4_v2 ($0.54/hour)
   - Check: Not below min_size, within allowed_sizes list
4. Apply resize via Azure API
5. Generate report: {cluster, old_size, new_size, avg_cpu, estimated_savings}
```

**Safety Guardrails:**
- Never downsize below `rightsize_min_size` (default: Standard_DS3_v2)
- Only downsize within `rightsize_allowed_sizes` list (prevent accidental GPU→CPU)
- Require 7 consecutive days < threshold (avoid reacting to temporary dips)
- Never auto-upsize (requires manual approval)

**Cost Savings Example:**
- Cluster downsized: DS5_v2 ($0.72/hr) → DS4_v2 ($0.54/hr)
- Savings: $0.18/hour × 730 hours/month = **$131/cluster/month**
- Typical scenario: 3 out of 10 clusters downsized = **$393/month**

---

## Role Design

### Role: `azure_ml_cost_optimization`

**Location:** `roles/azure_ml_cost_optimization/`

**Structure:**
```
roles/azure_ml_cost_optimization/
├── README.md
├── defaults/
│   └── main.yml  (all variables with defaults)
├── meta/
│   └── main.yml  (dependencies, galaxy metadata)
└── tasks/
    ├── main.yml  (operation dispatcher)
    ├── shutdown_compute.yml
    ├── startup_compute.yml
    ├── analyze_and_rightsize.yml
    ├── manage_ptu.yml
    ├── generate_roi_report.yml
    └── utils/
        ├── collect_metrics.yml  (shared: query Azure Monitor/ML)
        ├── calculate_costs.yml  (shared: cost calculations)
        └── validate_prerequisites.yml  (check permissions, API availability)
```

### Role Variables

**Core Configuration:**

```yaml
# Operation to perform
azure_ml_cost_optimization_operation: "shutdown_compute"
# Valid values:
#   - shutdown_compute
#   - startup_compute
#   - analyze_and_rightsize
#   - manage_ptu
#   - generate_roi_report

# Target scope
azure_resource_group: "ml-platform-prod"  # Required
azure_region: "eastus"  # Required

# Target resources (empty = all in resource group)
azure_ml_cost_optimization_workspaces: []  # List of workspace names
azure_ml_cost_optimization_compute_targets: []  # List of compute cluster names
azure_ml_cost_optimization_openai_accounts: []  # List of OpenAI account names
```

**Shutdown/Startup Behavior:**

```yaml
# Shutdown mode
azure_ml_cost_optimization_shutdown_mode: "graceful"
# Valid values:
#   - graceful: Wait for running jobs to complete (max 30 min timeout)
#   - immediate: Stop immediately, may interrupt jobs

# Job preservation
azure_ml_cost_optimization_preserve_running_jobs: true
# If true, skip clusters with active jobs during shutdown
```

**Right-Sizing Configuration:**

```yaml
# Enable/disable right-sizing
azure_ml_cost_optimization_rightsize_enabled: true

# CPU utilization threshold (%)
azure_ml_cost_optimization_rightsize_cpu_threshold: 30
# Downsize if average CPU < this for analysis window

# Analysis window (days)
azure_ml_cost_optimization_rightsize_analysis_days: 7

# Allowed VM sizes for auto-resize
azure_ml_cost_optimization_rightsize_allowed_sizes:
  - Standard_DS3_v2
  - Standard_DS4_v2
  - Standard_DS5_v2
  - Standard_NC6s_v3
  - Standard_NC12s_v3

# Minimum allowed size (never downsize below this)
azure_ml_cost_optimization_rightsize_min_size: "Standard_DS3_v2"
```

**PTU Management (Azure OpenAI):**

```yaml
# Target PTU utilization (%)
azure_ml_cost_optimization_ptu_target_utilization: 80

# Scale-down threshold (%)
azure_ml_cost_optimization_ptu_scale_down_threshold: 50
# Scale down PTU if utilization < this for 7 days
```

**EDA Override Behavior:**

```yaml
# Emergency mode (set by EDA rulebook)
azure_ml_cost_optimization_emergency_mode: false

# Budget alert action
azure_ml_cost_optimization_budget_alert_action: "shutdown_non_critical"
# Valid values:
#   - shutdown_all: Shutdown all clusters immediately
#   - shutdown_non_critical: Shutdown clusters not tagged critical=true
#   - alert_only: Send notification, no action
```

**ROI Tracking:**

```yaml
# Baseline monthly cost (USD) before automation
azure_ml_cost_optimization_roi_baseline_monthly_cost: 0

# Tracking start date (ISO 8601)
azure_ml_cost_optimization_roi_tracking_start_date: ""

# Report output path
azure_ml_cost_optimization_roi_report_path: "/tmp/roi_report_{{ ansible_date_time.date }}.md"
```

---

## Operations Implementation

### Operation 1: `shutdown_compute`

**Purpose:** Stop Azure ML compute clusters to eliminate idle costs.

**Task Flow:**

```yaml
# tasks/shutdown_compute.yml (pseudocode)
1. Validate prerequisites
2. Query Azure ML workspaces in resource group
3. For each workspace:
   - Get all compute clusters (or filter by compute_targets)
   - For each cluster:
     - Check provisioning_state (skip if already stopped)
     - If preserve_running_jobs=true:
       - Query active jobs on cluster
       - Skip if jobs running, log job IDs
     - If shutdown_mode=graceful:
       - Wait for current job to finish (max 30 min timeout)
     - Scale cluster to min_nodes=0 (triggers auto-stop)
     - Record action in audit log
4. Return summary: {clusters_stopped, clusters_skipped, reasons}
```

**Azure API Calls:**
- `azure_rm_resource_info` - List ML workspaces
- `azure_rm_resource` (GET) - Get compute cluster state and job status
- `azure_rm_resource` (PUT) - Update cluster min_nodes to 0

**Example Output:**
```
TASK [Shutdown compute clusters summary]
ok: [localhost] => 
  msg: |
    Shutdown complete:
    - Clusters stopped: 7
    - Clusters skipped: 2 (active jobs)
    - Total cost savings: $21.42/hour ($15,625/month at 14hr/day)
```

---

### Operation 2: `startup_compute`

**Purpose:** Start previously shutdown clusters and restore to configured settings.

**Task Flow:**

```yaml
# tasks/startup_compute.yml (pseudocode)
1. Validate prerequisites
2. Query Azure ML compute clusters
3. For each stopped cluster:
   - Read original min_nodes from cluster config (or default=1)
   - Scale cluster to min_nodes (triggers startup)
   - Optionally wait for provisioning_state=Succeeded
4. Return summary: {clusters_started}
```

**Azure API Calls:**
- `azure_rm_resource` (GET) - Get cluster configuration
- `azure_rm_resource` (PUT) - Update cluster min_nodes to original value

---

### Operation 3: `analyze_and_rightsize`

**Purpose:** Analyze utilization metrics and automatically downsize underutilized clusters.

**Task Flow:**

```yaml
# tasks/analyze_and_rightsize.yml (pseudocode)
1. Validate prerequisites (Azure Monitor access)
2. Collect metrics (shared utility: utils/collect_metrics.yml):
   - Query Azure Monitor Metrics API
   - Metric: "Percentage CPU"
   - Aggregation: Average
   - Granularity: 1 hour
   - Time range: Past 7 days
3. For each cluster:
   - Calculate average CPU across 7 days
   - If avg_cpu < rightsize_cpu_threshold (default 30%):
     - Determine current VM size (e.g., Standard_DS4_v2)
     - Find next smaller size in allowed_sizes list (e.g., Standard_DS3_v2)
     - Validate:
       - Not below min_size
       - Within allowed_sizes list
       - Not crossing GPU/CPU boundary
     - Update cluster VM size via Azure API
     - Calculate cost savings (shared utility: utils/calculate_costs.yml)
4. Generate report: [{cluster, old_size, new_size, avg_cpu, monthly_savings}]
5. Save report to file (optional)
```

**Azure API Calls:**
- `azure_rm_resource` (GET, Azure Monitor API) - Get CPU metrics
- `azure_rm_resource` (GET) - Get cluster current VM size
- `azure_rm_resource` (PUT) - Update cluster VM size

**Safety Guardrails:**
- Never downsize below `rightsize_min_size`
- Only downsize within `rightsize_allowed_sizes` list
- Require 7 consecutive days < threshold
- Never auto-upsize (log recommendation instead)

**Example Report:**
```markdown
## Right-Sizing Analysis Report
**Date:** 2026-09-09
**Resource Group:** ml-platform-prod

### Clusters Downsized:

| Cluster | Old Size | New Size | Avg CPU (7d) | Monthly Savings |
|---------|----------|----------|--------------|-----------------|
| ds-team-a-compute | Standard_DS5_v2 | Standard_DS4_v2 | 22% | $131 |
| ds-team-b-compute | Standard_DS4_v2 | Standard_DS3_v2 | 18% | $197 |

**Total Monthly Savings:** $328
```

---

### Operation 4: `manage_ptu`

**Purpose:** Optimize Azure OpenAI Provisioned Throughput Units based on utilization.

**Task Flow:**

```yaml
# tasks/manage_ptu.yml (pseudocode)
1. Validate prerequisites
2. For each Azure OpenAI account:
   - Query PTU utilization metric (past 7 days)
   - Calculate average utilization %
3. Decision logic:
   - If avg < scale_down_threshold (default 50%) for 7 days:
     - Reduce PTU capacity by 1 tier (e.g., 100 PTU → 50 PTU)
     - Log action and cost savings
   - If avg > target_utilization (default 80%) for 3 days:
     - Log recommendation to increase PTU
     - DO NOT auto-upsize (manual approval required)
4. Return report: [{account, current_ptu, new_ptu, avg_utilization, savings}]
```

**Azure API Calls:**
- `azure_rm_resource` (GET, Azure Monitor API) - Get PTU utilization metrics
- `azure_rm_resource` (GET) - Get current PTU capacity
- `azure_rm_resource` (PUT) - Update PTU capacity (downsize only)

**PTU Pricing Context:**
- 50 PTU: ~$2,500/month
- 100 PTU: ~$5,000/month
- 300 PTU: ~$15,000/month

**Cost Savings Example:**
- PTU reduced from 100 → 50
- Monthly savings: **$2,500**

---

### Operation 5: `generate_roi_report`

**Purpose:** Calculate cost savings vs baseline and generate ROI report.

**Task Flow:**

```yaml
# tasks/generate_roi_report.yml (pseudocode)
1. Validate prerequisites (Cost Management API access, baseline set)
2. Query Azure Cost Management API:
   - Current month-to-date cost (resource group scope)
   - Filter by tags: cost_center=ml-platform (optional)
   - Breakdown by resource type (compute, storage, OpenAI)
3. Calculate metrics:
   - baseline_cost (from variable)
   - current_cost (from API)
   - savings = baseline_cost - current_cost
   - savings_percent = (savings / baseline_cost) * 100
   - projected_annual_savings = savings * 12
4. Query audit log for actions taken:
   - Count shutdown events
   - Count rightsize events
   - Count PTU optimization events
5. Generate markdown report with:
   - Summary table (baseline, current, savings)
   - Breakdown by resource type
   - Actions taken this month
   - Cost trend chart (ASCII art or data for external visualization)
6. Save report to file
7. Optionally send via email/Slack (configurable)
```

**Azure API Calls:**
- `azure_rm_resource` (POST, Cost Management API) - Query cost data

**Example Report:**
```markdown
## ML Platform Cost Optimization - ROI Report
**Month:** September 2026  
**Baseline Monthly Cost:** $15,000  
**Current Month-to-Date Cost:** $8,200  
**Savings:** $6,800 (45%)  
**Projected Annual Savings:** $81,600  

### Cost Breakdown:

| Resource Type | Baseline | Current | Savings |
|---------------|----------|---------|---------|
| Compute Clusters | $10,000 | $4,500 | $5,500 |
| Azure OpenAI PTU | $5,000 | $2,500 | $2,500 |
| Storage | $0 | $1,200 | -$1,200 |

### Actions Taken This Month:
- 23 compute cluster shutdowns (avg 12 hours idle time saved/day)
- 3 clusters downsized (DS5_v2 → DS4_v2)
- Azure OpenAI PTU reduced 100 → 50 (low utilization detected)

### Cost Trend (Last 6 Months):
```
Month       | Cost   | vs Baseline
------------|--------|-------------
Apr 2026    | $15,200| +1%
May 2026    | $14,800| -1%
Jun 2026    | $11,500| -23% (automation enabled)
Jul 2026    | $9,100 | -39%
Aug 2026    | $8,500 | -43%
Sep 2026    | $8,200 | -45%
```
```

---

## Playbook Implementation

### Primary Playbook: `cost_optimization.yml`

**Location:** `playbooks/cost_optimization.yml`

**Structure:**

```yaml
---
- name: Azure ML/AI cost optimization
  hosts: localhost
  gather_facts: false

  vars_files:
    - vars/cost_optimization_vars.yml

  tasks:
    - name: Fail when required variables not defined
      ansible.builtin.fail:
        msg: "Required variable {{ item }} not defined"
      when: vars[item] is not defined
      loop:
        - operation
        - azure_resource_group

    - name: Run cost optimization operation
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: "{{ operation }}"
        # All other vars come from vars file or extra_vars
```

**Variables File:** `playbooks/vars/cost_optimization_vars.yml`

```yaml
---
# Default configuration for cost optimization playbook
azure_region: "eastus"

# Shutdown/startup defaults
azure_ml_cost_optimization_shutdown_mode: "graceful"
azure_ml_cost_optimization_preserve_running_jobs: true

# Right-sizing defaults
azure_ml_cost_optimization_rightsize_enabled: true
azure_ml_cost_optimization_rightsize_cpu_threshold: 30
azure_ml_cost_optimization_rightsize_analysis_days: 7
azure_ml_cost_optimization_rightsize_allowed_sizes:
  - Standard_DS3_v2
  - Standard_DS4_v2
  - Standard_DS5_v2
azure_ml_cost_optimization_rightsize_min_size: "Standard_DS3_v2"

# PTU defaults
azure_ml_cost_optimization_ptu_target_utilization: 80
azure_ml_cost_optimization_ptu_scale_down_threshold: 50

# ROI tracking (set to your baseline)
azure_ml_cost_optimization_roi_baseline_monthly_cost: 15000
azure_ml_cost_optimization_roi_tracking_start_date: "2026-06-01"
```

---

## AAP Integration

### Workflow Template 1: Scheduled Shutdown (Daily)

**Template Name:** `ML Cost Optimization - Nightly Shutdown`

**Schedule:** Cron `0 18 * * 1-5` (6pm weekdays)

**Survey Variables:**

```yaml
survey_name: "ML Cost Optimization - Shutdown"
questions:
  - variable: azure_resource_group
    question: "Resource group to shutdown?"
    type: text
    required: true
  
  - variable: shutdown_mode
    question: "Shutdown mode?"
    type: multiplechoice
    choices:
      - display: "Graceful (wait for jobs, max 30 min)"
        value: "graceful"
      - display: "Immediate (may interrupt jobs)"
        value: "immediate"
    default: "graceful"
  
  - variable: preserve_running_jobs
    question: "Preserve running jobs?"
    type: multiplechoice
    choices:
      - display: "Yes - skip clusters with active jobs"
        value: true
      - display: "No - shutdown all clusters"
        value: false
    default: true
```

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.cost_optimization`
- Extra vars: `operation: shutdown_compute`
- Credentials: Azure Service Principal with Contributor role
- Limit: `localhost`

---

### Workflow Template 2: Scheduled Startup (Daily)

**Template Name:** `ML Cost Optimization - Morning Startup`

**Schedule:** Cron `0 8 * * 1-5` (8am weekdays)

**Survey Variables:**

```yaml
survey_name: "ML Cost Optimization - Startup"
questions:
  - variable: azure_resource_group
    question: "Resource group to startup?"
    type: text
    required: true
  
  - variable: compute_targets
    question: "Specific clusters to start (comma-separated, blank = all)?"
    type: text
    required: false
```

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.cost_optimization`
- Extra vars: `operation: startup_compute`
- Credentials: Azure Service Principal
- Limit: `localhost`

---

### Workflow Template 3: Weekly Right-Sizing Analysis

**Template Name:** `ML Cost Optimization - Right-Sizing Analysis`

**Schedule:** Cron `0 2 * * 0` (2am Sunday)

**Survey Variables:**

```yaml
survey_name: "ML Cost Optimization - Right-Sizing"
questions:
  - variable: azure_resource_group
    question: "Resource group to analyze?"
    type: text
    required: true
  
  - variable: rightsize_cpu_threshold
    question: "CPU utilization threshold (%)?"
    type: multiplechoice
    choices:
      - display: "20% (aggressive downsizing)"
        value: 20
      - display: "30% (recommended)"
        value: 30
      - display: "40% (conservative)"
        value: 40
    default: 30
  
  - variable: rightsize_analysis_days
    question: "Analysis window (days)?"
    type: multiplechoice
    choices:
      - display: "7 days (recommended)"
        value: 7
      - display: "14 days (conservative)"
        value: 14
    default: 7
```

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.cost_optimization`
- Extra vars: `operation: analyze_and_rightsize`
- Credentials: Azure Service Principal + Monitoring Reader role
- Limit: `localhost`

---

### Workflow Template 4: PTU Optimization (Hourly)

**Template Name:** `ML Cost Optimization - PTU Management`

**Schedule:** Cron `0 * * * *` (every hour)

**Survey Variables:**

```yaml
survey_name: "ML Cost Optimization - PTU"
questions:
  - variable: azure_resource_group
    question: "Resource group containing OpenAI accounts?"
    type: text
    required: true
  
  - variable: openai_accounts
    question: "Specific OpenAI accounts (comma-separated, blank = all)?"
    type: text
    required: false
```

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.cost_optimization`
- Extra vars: `operation: manage_ptu`
- Credentials: Azure Service Principal
- Limit: `localhost`

---

### Workflow Template 5: Monthly ROI Report

**Template Name:** `ML Cost Optimization - ROI Report`

**Schedule:** Cron `0 9 1 * *` (9am 1st of month)

**Survey Variables:**

```yaml
survey_name: "ML Cost Optimization - ROI Report"
questions:
  - variable: azure_resource_group
    question: "Resource group to report on?"
    type: text
    required: true
  
  - variable: report_output_path
    question: "Report output path?"
    type: text
    default: "/tmp/roi_report_{{ ansible_date_time.date }}.md"
```

**Job Template Configuration:**
- Playbook: `cloud.azure_ops.cost_optimization`
- Extra vars: `operation: generate_roi_report`
- Credentials: Azure Service Principal + Cost Management Reader role
- Limit: `localhost`

---

## EDA Integration

### EDA Rulebook: `eda_cost_alerts.yml`

**Purpose:** Event-driven cost control triggered by Azure Cost Management events.

**Location:** Documented in reference architecture (not included in collection)

**Rulebook Example:**

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
          name: "ML Cost Optimization - Emergency Shutdown"
          organization: "Default"
          extra_vars:
            operation: "shutdown_compute"
            emergency_mode: true
            budget_alert_action: "shutdown_non_critical"
            azure_resource_group: "{{ event.data.resourceGroup }}"
    
    - name: Cost anomaly detected - generate immediate ROI report
      condition: event.data.costAnomaly == true
      action:
        run_job_template:
          name: "ML Cost Optimization - ROI Report"
          organization: "Default"
          extra_vars:
            operation: "generate_roi_report"
            alert_team: true
            azure_resource_group: "{{ event.data.resourceGroup }}"
```

### Azure Event Grid Setup

**Required Azure Resources:**

1. **Event Grid System Topic** (source: Azure Cost Management)
2. **Service Bus Namespace + Queue** (destination for events)
3. **Event Subscription** (connects Event Grid → Service Bus)

**Event Grid Configuration:**

```bash
# Create Event Grid system topic for cost management
az eventgrid system-topic create \
  --name cost-management-topic \
  --resource-group ml-platform-prod \
  --source /subscriptions/{subscription-id} \
  --topic-type Microsoft.CostManagement.Budgets

# Create Service Bus namespace and queue
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
```

**EDA Configuration:**

```yaml
# EDA controller configuration
EDA_SERVICE_BUS_CONNECTION: "Endpoint=sb://ml-cost-events.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=..."
```

### Hybrid Trigger Flow

**Normal Operation:**
```
6pm daily (scheduled) → Shutdown playbook runs → Graceful shutdown
8am daily (scheduled) → Startup playbook runs → Restore clusters
```

**Override Scenario (EDA):**
```
3pm (budget hits 80%) → EDA triggers emergency shutdown
  → Shutdown playbook runs (emergency_mode=true)
  → Immediate shutdown, skip graceful wait
  → Shutdown non-critical clusters only (tagged critical=false)
6pm (scheduled) → Shutdown playbook runs → No-op (already stopped)
```

---

## Error Handling & Validation

### Pre-flight Validation

**Validation Tasks:** `tasks/utils/validate_prerequisites.yml`

```yaml
- name: Validate Azure credentials by querying subscription info
  azure.azcollection.azure_rm_subscription_info:
  register: _subscription_info
  failed_when: _subscription_info.subscriptions | length == 0

- name: Verify resource group exists
  azure.azcollection.azure_rm_resourcegroup_info:
    name: "{{ azure_resource_group }}"
  register: _rg_info
  failed_when: _rg_info.resourcegroups | length == 0

- name: Set subscription facts
  ansible.builtin.set_fact:
    _subscription_id: "{{ _subscription_info.subscriptions[0].subscription_id }}"
    _tenant_id: "{{ _subscription_info.subscriptions[0].tenant_id }}"
```

### Operation-Specific Validations

| Operation | Validation Checks | Failure Behavior |
|-----------|------------------|------------------|
| `shutdown_compute` | Workspace exists, compute clusters exist | Fail if workspace not found; warn and continue if no clusters |
| `startup_compute` | Clusters exist and are stopped | Skip already-running clusters, warn if all running |
| `analyze_and_rightsize` | Azure Monitor API accessible, 7 days of metrics available | Fail if no metrics; skip clusters with incomplete data |
| `manage_ptu` | OpenAI account exists, PTU metrics available | Skip accounts without PTU provisioned |
| `generate_roi_report` | Cost Management API accessible, baseline cost set | Fail if API unavailable; warn if baseline=0 |

### Partial Failure Handling

**Pattern: Continue processing remaining resources on individual failures**

```yaml
- name: Shutdown compute clusters
  azure.azcollection.azure_rm_resource:
    # ... shutdown logic
  loop: "{{ _clusters }}"
  register: _shutdown_results
  ignore_errors: true  # Continue processing remaining clusters

- name: Report partial failures
  ansible.builtin.debug:
    msg: |
      Shutdown complete: {{ _shutdown_results.results | selectattr('failed', 'false') | list | length }} succeeded
      Failed: {{ _shutdown_results.results | selectattr('failed', 'true') | list | length }}

- name: Fail if all operations failed
  ansible.builtin.fail:
    msg: "All shutdown operations failed. Check Azure permissions and cluster states."
  when: _shutdown_results.results | selectattr('failed', 'false') | list | length == 0
```

### Common Error Scenarios

| Error | Root Cause | Recovery Action |
|-------|-----------|-----------------|
| "Cluster not found" | Cluster deleted externally | Skip with warning, continue to next cluster |
| "Insufficient permissions" | Service principal missing Contributor role | Fail with remediation steps (grant Contributor + Monitoring Reader) |
| "Active jobs running" | `preserve_running_jobs=true` but jobs found | Skip cluster, log job IDs, report in summary |
| "Metrics API throttled" | Too many API calls | Implement exponential backoff, retry 3 times (5s, 15s, 45s delays) |
| "Invalid VM size transition" | Attempt to resize GPU→CPU | Skip with error, log invalid transition |
| "Cost Management API unavailable" | Azure service outage | Retry 3 times with 30s delay, then fail with report generation skipped |
| "PTU not provisioned" | OpenAI account doesn't use PTU | Skip account with info message |

### Audit Logging

**Audit Log Structure:**

```yaml
# Every operation logs state changes
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
  
  - timestamp: "2026-09-09T18:06:15Z"
    operation: "shutdown_compute"
    cluster: "ds-team-b-compute"
    workspace: "team-b-ml-workspace"
    action: "skipped"
    reason: "active_jobs_running"
    job_ids: ["job-12345", "job-67890"]
```

**Audit Log Output (Optional):**

```yaml
# Save audit log to file (configurable)
- name: Write audit log to file
  ansible.builtin.copy:
    content: "{{ _audit_log | to_nice_yaml }}"
    dest: "/var/log/azure_ml_cost_optimization_{{ ansible_date_time.date }}.yml"
  when: azure_ml_cost_optimization_enable_audit_log | default(false)
```

---

## ROI Calculation Framework

### Establishing Baseline

**Step 1: Measure Pre-Automation Costs**

```bash
# Query Azure Cost Management API for past 3 months average
az costmanagement query \
  --type ActualCost \
  --dataset-aggregation '{"totalCost":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping name="ResourceGroup" type="Dimension" \
  --timeframe Custom \
  --time-period from="2026-03-01" to="2026-05-31" \
  --scope "/subscriptions/{subscription-id}"

# Calculate baseline
baseline_monthly_cost = avg(March, April, May costs)
```

**Step 2: Set Baseline Variable**

```yaml
# playbooks/vars/cost_optimization_vars.yml
azure_ml_cost_optimization_roi_baseline_monthly_cost: 15000  # USD
azure_ml_cost_optimization_roi_tracking_start_date: "2026-06-01"  # Automation enabled
```

### Sample ROI Scenarios

#### Scenario 1: Small Team (5 Data Scientists)

**Infrastructure:**
- 3 GPU clusters (Standard_NC6s_v3: $3.06/hour)
- Azure OpenAI (Pay-as-you-go: ~$500/month)
- Storage: Minimal (~$100/month)

**Baseline Monthly Cost:** $12,000
- Compute: 3 clusters × 730 hours × $3.06 = $6,701
- Clusters running 24/7 (assumed 50% actual utilization)
- Estimated idle time: 50% × 730 hours = 365 hours/month

**Actions Taken (Post-Automation):**
- Nightly shutdown (6pm-8am weekdays): 14 hours/day × 5 days × 4.3 weeks = 301 hours/month saved
- Weekend shutdown (Saturday-Sunday): 48 hours × 4.3 weeks = 206 hours/month saved
- Total idle time eliminated: 507 hours/month

**Post-Automation Monthly Cost:** $6,500
- Compute: 3 clusters × (730 - 507) hours × $3.06 = $2,048
- OpenAI: $500 (no change)
- Storage: $100 (growing with usage)
- Additional: Right-sizing downsized 1 cluster (DS5_v2 → DS4_v2): $131 saved

**Monthly Savings:** $5,500 (46%)  
**Annual Savings:** $66,000  

---

#### Scenario 2: Medium Team (15 Data Scientists)

**Infrastructure:**
- 10 ML compute clusters (mixed: 6 × DS4_v2, 4 × NC6s_v3)
- Azure OpenAI (100 PTU: $5,000/month)
- Storage: Growing (~$500/month)

**Baseline Monthly Cost:** $35,000
- CPU clusters: 6 × 730 × $0.54 = $2,365
- GPU clusters: 4 × 730 × $3.06 = $8,935
- OpenAI PTU: $5,000
- Storage: $500
- Assumed 40% actual utilization

**Actions Taken (Post-Automation):**
- Scheduled shutdown: 507 hours/month saved (same pattern as Scenario 1)
- Right-sizing: 3 clusters downsized (DS5_v2 → DS4_v2): $393/month saved
- PTU optimization: 100 PTU → 50 PTU (utilization <50%): $2,500/month saved
- EDA: 1 emergency shutdown prevented budget overrun (saved ~$2,000)

**Post-Automation Monthly Cost:** $19,000
- Compute (after shutdown + rightsize): $4,500
- OpenAI PTU (optimized): $2,500
- Storage: $500 (growing)
- Additional overhead: $500

**Monthly Savings:** $16,000 (46%)  
**Annual Savings:** $192,000  

---

#### Scenario 3: Large Enterprise (50+ Data Scientists, Multi-Region)

**Infrastructure:**
- 40 ML compute clusters (multi-region: East US, West Europe)
- 5 Azure OpenAI accounts (mixed: 3 × 100 PTU, 2 pay-as-you-go)
- Storage: Large datasets (~$3,000/month)

**Baseline Monthly Cost:** $150,000
- Compute: 40 clusters × 730 × avg($1.50/hour) = $43,800
- OpenAI: 3 × $5,000 + 2 × $2,000 = $19,000
- Storage: $3,000
- Assumed 30% actual utilization (high idle waste)

**Actions Taken (Post-Automation):**
- Scheduled shutdown (regional): 507 hours/month saved × 40 clusters
- Right-sizing: 12 clusters downsized, 5 clusters upsized (after initial over-provisioning): Net $1,500/month saved
- PTU optimization: 2 accounts downsized (100 → 50 PTU): $5,000/month saved
- EDA: 2 emergency shutdowns prevented budget overruns (saved ~$8,000)
- Policy enforcement: Prevented 3 unauthorized GPU cluster deployments (saved ~$10,000)

**Post-Automation Monthly Cost:** $82,000
- Compute (after shutdown + rightsize): $18,000
- OpenAI (optimized): $14,000
- Storage: $3,000 (growing)
- Additional overhead: $2,000

**Monthly Savings:** $68,000 (45%)  
**Annual Savings:** $816,000  

---

### ROI Tracking Methodology

**Monthly Report Generation:**

```bash
# Run ROI report playbook (automated on 1st of month)
ansible-playbook cloud.azure_ops.cost_optimization \
  -e operation=generate_roi_report \
  -e azure_resource_group=ml-platform-prod
```

**Report Metrics:**

1. **Cost Metrics:**
   - Baseline monthly cost (from variable)
   - Current month-to-date cost (from Cost Management API)
   - Savings (baseline - current)
   - Savings percentage
   - Projected annual savings

2. **Action Metrics:**
   - Number of shutdown events
   - Number of startup events
   - Number of clusters rightsized (up/down)
   - Number of PTU optimizations
   - Number of EDA triggers

3. **Cost Breakdown:**
   - Compute costs (by cluster, by workspace)
   - OpenAI costs (by account)
   - Storage costs
   - Other costs

4. **Trend Analysis:**
   - Month-over-month cost comparison (past 6 months)
   - Cost per data scientist (if team size tracked)
   - Cost per ML job (if job count tracked)

**Cost Calculator Template:**

```yaml
# File: docs/cost_calculator_template.yml
# Fill in your values to estimate ROI

# Current infrastructure
num_cpu_clusters: 6
cpu_cluster_vm_size: "Standard_DS4_v2"  # $0.54/hour
cpu_cluster_utilization_percent: 40

num_gpu_clusters: 4
gpu_cluster_vm_size: "Standard_NC6s_v3"  # $3.06/hour
gpu_cluster_utilization_percent: 30

num_openai_accounts: 1
openai_ptu_capacity: 100  # $5,000/month
openai_ptu_utilization_percent: 45

# Automation parameters
shutdown_hours_per_day: 14  # 6pm-8am = 14 hours
shutdown_days_per_week: 5   # Weekdays only
weekend_shutdown: true      # Full weekend shutdown

# Calculated savings (filled by playbook)
monthly_baseline_cost: 0
monthly_projected_cost: 0
monthly_savings: 0
annual_savings: 0
```

---

## Testing Strategy

### Unit Testing (Playbook Validation)

```bash
# Syntax validation
ansible-playbook --syntax-check playbooks/cost_optimization.yml

# Linting
ansible-lint playbooks/cost_optimization.yml
ansible-lint roles/azure_ml_cost_optimization/

# Variable validation (check mode)
ansible-playbook playbooks/cost_optimization.yml --check \
  -e operation=shutdown_compute \
  -e azure_resource_group=test-rg
```

### Integration Testing Scenarios

**Scenario 1: Shutdown/Startup Cycle**
```yaml
test_steps:
  - name: "Setup - Create test ML workspace with compute"
    operation: create
    resources:
      - ML workspace with 2 compute clusters (Standard_DS3_v2)
      - Both clusters running (min_nodes=1)
  
  - name: "Execute - Graceful shutdown"
    operation: shutdown_compute
    vars:
      shutdown_mode: graceful
      preserve_running_jobs: false
    validate:
      - Both clusters scaled to min_nodes=0
      - Clusters in stopped state within 5 minutes
      - Audit log contains 2 shutdown entries
  
  - name: "Execute - Startup"
    operation: startup_compute
    validate:
      - Both clusters restored to min_nodes=1
      - Clusters in running state within 10 minutes
```

**Scenario 2: Right-Sizing with Metrics**
```yaml
test_steps:
  - name: "Setup - Create underutilized cluster"
    operation: create
    resources:
      - Cluster with Standard_DS4_v2, low CPU usage (<20% for 7 days)
      - Mock Azure Monitor metrics (simulate 7 days of data)
  
  - name: "Execute - Analyze and rightsize"
    operation: analyze_and_rightsize
    vars:
      rightsize_cpu_threshold: 30
      rightsize_allowed_sizes: [Standard_DS3_v2, Standard_DS4_v2, Standard_DS5_v2]
    validate:
      - Cluster resized from DS4_v2 to DS3_v2
      - Report shows estimated savings
      - No resize below min_size
```

**Scenario 3: EDA Emergency Shutdown**
```yaml
test_steps:
  - name: "Setup - Multiple running clusters (critical + non-critical)"
    resources:
      - Cluster A (tagged: critical=true)
      - Cluster B (tagged: critical=false)
      - Cluster C (tagged: critical=false)
  
  - name: "Execute - Emergency shutdown (non-critical only)"
    operation: shutdown_compute
    vars:
      emergency_mode: true
      budget_alert_action: shutdown_non_critical
    validate:
      - Cluster A still running
      - Clusters B and C stopped
      - Emergency flag logged in audit trail
```

**Scenario 4: PTU Management**
```yaml
test_steps:
  - name: "Setup - Azure OpenAI account with PTU"
    resources:
      - OpenAI account with 100 PTU
      - Mock utilization metrics (avg 45% for 7 days)
  
  - name: "Execute - PTU optimization"
    operation: manage_ptu
    vars:
      ptu_scale_down_threshold: 50
    validate:
      - PTU reduced from 100 to 50
      - Report shows utilization below threshold
      - Cost savings projection included
```

**Scenario 5: ROI Report Generation**
```yaml
test_steps:
  - name: "Setup - Cost data with baseline"
    vars:
      roi_baseline_monthly_cost: 15000
      roi_tracking_start_date: "2026-09-01"
    mock_data:
      - Current month-to-date cost: $8200
      - 15 shutdown events logged
      - 2 rightsize events logged
  
  - name: "Execute - Generate ROI report"
    operation: generate_roi_report
    validate:
      - Report file created
      - Savings calculated: $6800 (45%)
      - Projected annual savings: $81,600
      - Action summary includes shutdown and rightsize counts
```

### Validation Checklist

**Idempotency:**
- [ ] Running shutdown twice on stopped clusters produces no errors
- [ ] Running startup twice on running clusters produces no errors
- [ ] Right-sizing analysis with no changes produces empty report

**Safety:**
- [ ] Clusters with running jobs are skipped when `preserve_running_jobs=true`
- [ ] Right-sizing never downsizes below `min_size`
- [ ] Emergency shutdown respects critical resource tags

**Error Handling:**
- [ ] Partial failures (some clusters succeed, some fail) produce summary report
- [ ] Missing metrics data fails gracefully with clear error message
- [ ] Invalid operation parameter fails immediately with helpful message

**Performance:**
- [ ] Shutdown of 10 clusters completes within 15 minutes
- [ ] Metrics collection for 7 days doesn't timeout
- [ ] ROI report generation completes within 2 minutes

---

## Documentation Deliverables

### 1. Playbook Documentation

**File:** `playbooks/COST_OPTIMIZATION.md`

**Sections:**
- Overview - Architecture diagram, business value, user stories
- Prerequisites - Azure subscription, required resource providers, service principal permissions (Contributor + Monitoring Reader), AAP version
- Variables Reference - Complete variable list with descriptions, defaults, validation rules
- Usage Examples - Command-line examples for each operation
- AAP Integration - Survey specs, workflow templates, scheduling configuration
- EDA Integration - Rulebook patterns, Azure Event Grid setup, Service Bus configuration
- Cost Optimization Patterns - Scheduled lifecycle, event-driven override, continuous right-sizing
- ROI Framework - How to measure savings, baseline setup, sample scenarios
- Troubleshooting - Common errors, remediation steps, permission issues

### 2. Role Documentation

**File:** `roles/azure_ml_cost_optimization/README.md`

**Sections:**
- Role description and capabilities
- Requirements (Azure permissions: Contributor + Monitoring Reader + Cost Management Reader, API access)
- Role variables (all operations)
- Dependencies (none)
- Example playbook usage for each operation
- License

### 3. ROI Calculation Framework

**File:** `docs/cost_optimization_roi_framework.md`

**Content:**
- Baseline establishment methodology
- Tracking methodology
- Sample scenarios (3 scenarios with calculations: small/medium/large teams)
- Cost calculator template
- Reporting templates

### 4. AAP Survey Specifications

**Directory:** `docs/aap_surveys/`

**Files:**
- `cost_optimization_shutdown_survey.json` - Survey for manual shutdown trigger
- `cost_optimization_rightsize_survey.json` - Survey for right-sizing analysis
- `cost_optimization_ptu_survey.json` - Survey for PTU management
- `workflow_templates.md` - Step-by-step guide to configure schedules in AAP UI

### 5. EDA Integration Guide

**File:** `docs/eda_cost_alerts_setup.md`

**Content:**
- Azure Event Grid setup for Cost Management events
- Service Bus queue configuration
- EDA rulebook examples (budget threshold, anomaly detection)
- Testing EDA triggers
- Troubleshooting EDA connectivity

---

## Success Criteria

### Functional Requirements (from Jira DoD)

- [ ] Compute lifecycle playbooks (shutdown, startup, resize) tested and documented
- [ ] EDA cost-event integration pattern documented
- [ ] ROI framework with at least 3 sample scenarios
- [ ] PTU/reserved capacity management pattern included
- [ ] Cost savings projections validated with realistic data (30-50% reduction claim)

### Additional Quality Requirements

**Functional:**
- [ ] `shutdown_compute` stops all clusters in resource group within 15 minutes (graceful mode)
- [ ] `startup_compute` restarts clusters and restores min_nodes settings
- [ ] `analyze_and_rightsize` correctly identifies underutilized clusters and downsizes
- [ ] `manage_ptu` scales down PTU when utilization < threshold for 7 days
- [ ] `generate_roi_report` produces accurate savings calculation vs baseline
- [ ] All operations are idempotent (safe to run multiple times)

**Documentation:**
- [ ] Playbook documentation follows existing `MLOPS_LIFECYCLE.md` pattern
- [ ] Role README includes example usage for all 5 operations
- [ ] ROI framework includes 3 sample scenarios with realistic projections
- [ ] Architecture diagrams included (ASCII art matches existing collection style)
- [ ] Troubleshooting section has remediation steps for common errors

**Quality:**
- [ ] Passes `ansible-lint` with no errors
- [ ] All operations handle partial failures gracefully
- [ ] Error messages are actionable (include remediation steps)
- [ ] Follows existing collection patterns (naming, variables, role structure)

---

## Implementation Phases

### Phase 1: Core Role Development (2-3 days)
- [ ] Create role directory structure
- [ ] Implement `shutdown_compute` operation
- [ ] Implement `startup_compute` operation
- [ ] Implement shared utility tasks (validate, collect_metrics, calculate_costs)
- [ ] Create defaults/main.yml with all variables

### Phase 2: Advanced Operations (2-3 days)
- [ ] Implement `analyze_and_rightsize` operation
- [ ] Implement `manage_ptu` operation
- [ ] Implement `generate_roi_report` operation
- [ ] Add error handling and partial failure logic
- [ ] Add audit logging

### Phase 3: Playbook & Integration (1-2 days)
- [ ] Create primary playbook `cost_optimization.yml`
- [ ] Create vars file `cost_optimization_vars.yml`
- [ ] Test all operations via playbook

### Phase 4: Documentation (2-3 days)
- [ ] Write `playbooks/COST_OPTIMIZATION.md`
- [ ] Write `roles/azure_ml_cost_optimization/README.md`
- [ ] Write `docs/cost_optimization_roi_framework.md`
- [ ] Create AAP survey JSON files
- [ ] Write `docs/eda_cost_alerts_setup.md`

### Phase 5: Testing & Validation (1-2 days)
- [ ] Run integration tests (all 5 scenarios)
- [ ] Validate idempotency
- [ ] Validate error handling
- [ ] Fix any issues found during testing

**Total Estimated Effort:** 8-13 days

---

## Future Enhancements

### Short-Term (Next Quarter)
- **Azure Policy integration** - Enforce allowed VM sizes, prevent unauthorized GPU deployments
- **Slack/Teams notifications** - Send cost alerts and ROI reports to team channels
- **Multi-subscription support** - Optimize costs across multiple Azure subscriptions
- **Cost anomaly detection** - Machine learning-based anomaly detection beyond budget thresholds

### Medium-Term (Next 6 Months)
- **Reserved instance recommendations** - Analyze usage patterns and recommend RI purchases
- **Spot instance integration** - Migrate non-critical workloads to Azure Spot VMs
- **GPU utilization tracking** - Track GPU-specific metrics (not just CPU) for right-sizing
- **Cost allocation by project** - Tag-based cost tracking per ML project/experiment

### Long-Term (Next Year)
- **Multi-cloud cost optimization** - Extend to AWS SageMaker, GCP Vertex AI
- **FinOps dashboard** - Real-time cost visualization and forecasting
- **Automated budget rebalancing** - Dynamic budget allocation based on team priorities
- **Carbon footprint tracking** - Measure and optimize ML workload carbon emissions

---

## Approval

**Design Reviewed By:** [User]  
**Date:** 2026-09-09  
**Status:** Approved for Implementation  

**Next Step:** Invoke `writing-plans` skill to create implementation plan.
