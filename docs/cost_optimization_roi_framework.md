# Azure ML Cost Optimization - ROI Calculation Framework

This document provides detailed guidance on establishing ROI baselines, tracking cost savings, and measuring the financial impact of the Azure ML cost optimization solution.

## Table of Contents

1. [Baseline Establishment](#baseline-establishment)
2. [Sample ROI Scenarios](#sample-roi-scenarios)
3. [ROI Tracking Methodology](#roi-tracking-methodology)
4. [Cost Calculator Template](#cost-calculator-template)
5. [Reporting Templates](#reporting-templates)

---

## Baseline Establishment

### Step 1: Measure Pre-Automation Costs

Before implementing automation, establish your current monthly infrastructure costs. This baseline will be compared against post-automation costs to calculate savings.

**Command:** Query Azure Cost Management API for past 3 months average

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Query costs for past 3 months (adjust dates as needed)
az costmanagement query create \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --timeframe Custom \
  --time-period from="2026-03-01" to="2026-05-31" \
  --dataset-aggregation totalCost="{name: 'Cost', function: 'Sum'}" \
  --dataset-grouping name="ResourceGroup" type="Dimension" \
  --dataset-granularity "Monthly" \
  --type "ActualCost"
```

**Manual Cost Calculation:**

If using the Azure Portal Cost Management:
1. Navigate to **Cost Management** > **Cost Analysis**
2. Set grouping to **Resource Group**
3. Select time period: Last 3 months (e.g., March-May 2026)
4. Filter to ML-related resources (workspaces, compute clusters, storage)
5. Calculate average monthly cost

**Example Baseline Calculation:**

```
March 2026 costs:   $14,200
April 2026 costs:   $15,100
May 2026 costs:     $15,600
─────────────────────────────
Average baseline:   $15,300/month
```

### Step 2: Set Baseline Variable in Playbook

Update the playbook variables file with your calculated baseline:

```yaml
# playbooks/vars/cost_optimization_vars.yml
azure_ml_cost_optimization_roi_baseline_monthly_cost: 15300  # USD (from Step 1)
azure_ml_cost_optimization_roi_tracking_start_date: "2026-06-01"  # Start of automation
```

### Step 3: Document Infrastructure Details

Record your current infrastructure to support ROI analysis:

```yaml
# docs/cost_optimization/infrastructure_baseline.yml
# Fill in your values for reference during ROI analysis

infrastructure:
  compute:
    - name: "GPU Cluster 1"
      vm_size: "Standard_NC6s_v3"
      num_nodes: 4
      hourly_cost: 12.24  # $3.06/hour per node
      estimated_utilization: 35%
      estimated_daily_idle_hours: 15
    
    - name: "CPU Cluster 1"
      vm_size: "Standard_DS5_v2"
      num_nodes: 2
      hourly_cost: 1.44   # $0.72/hour per node
      estimated_utilization: 40%
      estimated_daily_idle_hours: 14
  
  openai:
    - name: "Azure OpenAI Account 1"
      ptu_capacity: 100
      monthly_cost: 5000
      estimated_utilization: 45%
  
  storage:
    - name: "ML Platform Storage"
      monthly_cost: 500

  summary:
    total_clusters: 2
    total_monthly_cost: "{{ compute_cost + openai_cost + storage_cost }}"
```

---

## Sample ROI Scenarios

### Scenario 1: Small Team (5 Data Scientists)

**Use this scenario if:** Your team has 3-5 ML workspaces with a mix of CPU and GPU compute.

#### Infrastructure

```
Compute Resources:
  • 3 GPU clusters (Standard_NC6s_v3 @ $3.06/hour each)
  • Total nodes: 12 (4 nodes per cluster)
  • Hourly cost: $12.24 × 3 = $36.72/hour

Azure Services:
  • OpenAI (pay-as-you-go): ~$500/month
  • Storage (datasets): ~$100/month

Baseline Assumptions:
  • Clusters running 24/7 (730 hours/month)
  • Actual utilization: 50% (jobs running 50% of the time)
  • Estimated idle compute: 50% × 730 = 365 hours/month waste
```

#### Baseline Monthly Cost Breakdown

```
GPU compute (24/7):       730 hours × $36.72  = $26,806
OpenAI (pay-as-you-go):                        $500
Storage:                                        $100
─────────────────────────────────────────────────────
TOTAL BASELINE:                              $27,406/month
```

#### Actions Taken (Post-Automation)

```
Scheduled Shutdown (Nightly + Weekend):
  • Shutdown: 6pm weekdays, all day Saturday/Sunday
  • Startup: 8am weekdays
  • Idle time elimination:
    - Weekday nights: 14 hours/day × 5 days × 4.3 weeks = 301 hours/month
    - Weekends: 48 hours × 4.3 weeks = 206 hours/month
    - Total saved: 507 hours/month

Right-Sizing:
  • 1 GPU cluster identified as underutilized (avg CPU 22% over 7 days)
  • Candidates for downsizing: None (GPUs can't be downsized without replacing nodes)
  • Skip GPU downsize, monitor CPU clusters instead

Optimization Results:
  • GPU uptime reduced: 730 → 223 hours/month
  • New GPU compute cost: 223 × $36.72 = $8,190
  • Savings from shutdown: $26,806 - $8,190 = $18,616/month
```

#### Post-Automation Monthly Cost

```
GPU compute (223 hours):  223 × $36.72         = $8,190
OpenAI (pay-as-you-go):                        $500
Storage (no change):                           $100
─────────────────────────────────────────────────────
TOTAL POST-AUTOMATION:                       $8,790/month

Monthly Savings:    $27,406 - $8,790 = $18,616 (68%)
Annual Savings:     $18,616 × 12 = $223,392
```

**ROI Timeline:**
- AAP setup cost: ~$2,000 (one-time)
- Payback period: 2.6 hours of monthly savings (essentially immediate)

---

### Scenario 2: Medium Team (15 Data Scientists)

**Use this scenario if:** Your team spans multiple projects with diverse compute needs (CPU + GPU).

#### Infrastructure

```
Compute Resources:
  • 6 CPU clusters (Standard_DS4_v2 @ $0.54/hour)
    - 3 clusters × 2 nodes = 6 nodes running
  • 4 GPU clusters (Standard_NC6s_v3 @ $3.06/hour)
    - 4 clusters × 4 nodes = 16 nodes running
  • Total hourly cost: (6 × $0.54) + (16 × $3.06) = $52.44/hour

Azure Services:
  • Azure OpenAI (100 PTU): $5,000/month
  • Storage (growing datasets): $500/month

Baseline Assumptions:
  • All clusters running 24/7
  • Actual job utilization: 40% (less efficient than small team)
  • Estimated idle time: 60% × 730 = 438 hours/month waste
  • PTU utilization: 45% (significant over-provisioning)
```

#### Baseline Monthly Cost Breakdown

```
CPU compute (24/7):       (6 × 730) × $0.54        = $2,365
GPU compute (24/7):       (16 × 730) × $3.06       = $35,635
Azure OpenAI PTU:                                   = $5,000
Storage:                                            = $500
─────────────────────────────────────────────────────────────
TOTAL BASELINE:                                   = $43,500/month
```

#### Actions Taken (Post-Automation)

```
Scheduled Shutdown:
  • Same pattern as Scenario 1: 507 hours/month saved
  • CPU idle time saved: 507 × $0.54 = $274/month
  • GPU idle time saved: 507 × $3.06 = $1,551/month
  • Total shutdown savings: $1,825/month

Right-Sizing Analysis (7-day CPU threshold: 30%):
  • Cluster A: avg CPU 22% → resize DS5_v2 → DS4_v2 (-$0.18/hr)
  • Cluster B: avg CPU 18% → resize DS4_v2 → DS3_v2 (-$0.12/hr)
  • Cluster C: avg CPU 35% → no change (above threshold)
  • Monthly right-size savings: (0.18 + 0.12) × 730 × 2 = $197/month

PTU Optimization:
  • Current utilization: 45% (below 50% scale-down threshold)
  • Action: Scale down 100 PTU → 50 PTU
  • Monthly PTU savings: $2,500

Emergency Shutdown (EDA event):
  • 1 budget threshold event during month (at 80% of budget)
  • Emergency shutdown of non-critical clusters 3 hours early
  • Additional savings: ~$2,000
```

#### Post-Automation Monthly Cost

```
CPU compute (223 hrs):    (6 × 223) × $0.54        = $722
GPU compute (223 hrs):    (16 × 223) × $3.06       = $10,930
Azure OpenAI PTU (50):                             = $2,500
Storage (growing):                                 = $500
─────────────────────────────────────────────────────────────
TOTAL POST-AUTOMATION:                           = $14,652/month

Monthly Savings:    $43,500 - $14,652 = $28,848 (66%)
Annual Savings:     $28,848 × 12 = $346,176
```

**Key Insights:**
- Scheduled shutdown is the largest savings driver ($1,825/month)
- PTU optimization provides significant savings ($2,500/month for this scenario)
- Right-sizing provides incremental gains ($197/month)
- EDA event-driven actions prevent budget overruns

---

### Scenario 3: Large Enterprise (50+ Data Scientists, Multi-Region)

**Use this scenario if:** Your organization operates at scale with multiple regions and reserved capacity.

#### Infrastructure

```
Compute Resources (East US):
  • 20 CPU clusters (mixed sizes, avg: $0.54/hour)
  • 15 GPU clusters (mixed sizes, avg: $3.06/hour)
  • Total hourly cost: $100+/hour

Compute Resources (West Europe):
  • 10 CPU clusters
  • 8 GPU clusters
  • Total hourly cost: $60+/hour

Azure OpenAI Accounts (Global):
  • Account 1 (East US): 100 PTU = $5,000/month
  • Account 2 (East US): 100 PTU = $5,000/month
  • Account 3 (East US): 50 PTU = $2,500/month
  • Account 4 (West EU): 100 PTU = $5,000/month
  • Account 5 (Pay-as-you-go): $2,000/month
  • Total OpenAI: $19,500/month

Storage (Global, growing):
  • Enterprise datasets: $3,000/month

Total Hourly Infrastructure Cost: ~$200/hour
Baseline Assumptions:
  • Clusters running 24/7 across time zones
  • Actual utilization: 30% (typical for large orgs with varied workloads)
  • PTU utilization varies: 45-55% (over-provisioned for capacity)
```

#### Baseline Monthly Cost Breakdown

```
CPU compute (730 hrs × 35 clusters × avg $0.54):  $13,741
GPU compute (730 hrs × 23 clusters × avg $3.06):  $51,444
Azure OpenAI PTU (consolidated):                   $19,500
Storage (consolidated):                            $3,000
─────────────────────────────────────────────────────────────
TOTAL BASELINE:                                   $87,685/month
```

#### Actions Taken (Post-Automation, 6-Month Impact)

```
Month 1-3: Scheduled Shutdown Rollout
  • Phased implementation across regions
  • Shutdown pattern: 507 hours/month idle time eliminated
  • Compute savings (CPU): 507 × 35 × $0.54 = $9,547/month
  • Compute savings (GPU): 507 × 23 × $3.06 = $35,762/month
  • Subtotal: $45,309/month

Month 2-4: Right-Sizing Analysis & Implementation
  • Analysis of 40+ clusters over 7-day windows
  • Identified downsizing candidates: 12 CPU clusters, 5 GPU clusters
  • Phase 1 (Month 2): 8 clusters downsized
    - 5 CPU downsizes (avg $0.18/hr saving): 5 × $0.18 × 730 = $657
    - 3 GPU downsizes (avg $0.60/hr saving): 3 × $0.60 × 730 = $1,314
    - Subtotal: $1,971/month
  • Phase 2 (Month 4): Remaining 9 clusters downsized
    - Subtotal: $2,831/month
  • Total right-sizing savings (stabilized): $4,802/month

Month 2-6: PTU Optimization
  • Account 1: 100 PTU → 75 PTU (util: 52% → 67%, $1,250 savings)
  • Account 2: 100 PTU → 50 PTU (util: 45% → 60%, $2,500 savings)
  • Account 3: 50 PTU → 25 PTU (util: 35% → 47%, $1,250 savings)
  • Account 4: Unchanged (utilization at 75%)
  • Account 5: Monitor pay-as-you-go (recommend reserved)
  • Total PTU savings (stabilized): $5,000/month

Month 1-6: EDA Event-Driven Actions
  • Budget threshold alerts: 3 triggered
  • Emergency shutdowns prevented budget overruns: $8,000-$12,000/month
  • Policy enforcement: Prevented 5 unauthorized GPU deployments
  • Value: ~$10,000/month (average)

Month 6: Policy & Enforcement
  • Azure Policy enforced: No more manual intervention for compliance
  • Slack/Teams notifications: Real-time cost alerts
  • Spot VM migration: Non-critical workloads → Spot instances (-$2,000/month)
```

#### Post-Automation Monthly Cost (Steady State)

```
CPU compute (223 hrs):    223 × 35 × $0.54         = $4,204
GPU compute (223 hrs):    223 × 23 × $3.06         = $15,668
Azure OpenAI PTU (optimized):                      = $14,500
Storage (consolidated, growing):                  = $3,000
Spot VM instances (non-critical):                 = -$2,000
─────────────────────────────────────────────────────────────
TOTAL POST-AUTOMATION:                           = $35,372/month

Monthly Savings:    $87,685 - $35,372 = $52,313 (60%)
Annual Savings:     $52,313 × 12 = $627,756
6-Month Payback ROI: ($627,756 - $50,000 one-time) / $50,000 = 11.55x
```

**Implementation Cost Breakdown:**
```
Ansible Automation Platform: $30,000 (annual)
EDA licensing: $10,000 (annual)
Professional services: $10,000 (implementation)
─────────────────────────────────────────
Total implementation cost: $50,000 (one-time + annual)

Payback period: 1.1 months (after which savings exceed investment)
```

---

## ROI Tracking Methodology

### Monthly Report Generation

The `generate_roi_report` operation runs on a monthly schedule (recommended: 1st of month at 9am):

```bash
# Manual execution (for ad-hoc reports)
ansible-playbook cloud.azure_ops.cost_optimization \
  -e operation=generate_roi_report \
  -e azure_resource_group=ml-platform-prod \
  -e azure_ml_cost_optimization_roi_baseline_monthly_cost=15300
```

### Report Metrics (What Gets Tracked)

#### 1. Cost Metrics

```yaml
metrics:
  baseline_monthly_cost:        15300    # From setup (e.g., average of pre-automation)
  current_month_actual_cost:    8200     # From Cost Management API
  monthly_savings_usd:          7100     # baseline - current
  monthly_savings_percent:      46.4%    # savings / baseline × 100
  projected_annual_savings:     85200    # monthly_savings × 12
```

#### 2. Action Metrics

```yaml
actions_taken:
  shutdown_events:              23       # Number of shutdown operations
  startup_events:               21       # Number of startup operations
  clusters_rightsized_down:     3        # Downsized due to low utilization
  clusters_rightsized_up:       0        # Upsized (manual approval)
  ptu_optimizations:            1        # PTU scale-down events
  eda_triggers:                 2        # Emergency shutdowns from EDA
```

#### 3. Cost Breakdown

```yaml
cost_breakdown:
  compute_clusters:
    baseline:                   10000
    current:                    4500
    savings:                    5500
  
  azure_openai_ptu:
    baseline:                   5000
    current:                    2500
    savings:                    2500
  
  storage:
    baseline:                   0
    current:                    1200      # Growing with data
    delta:                      -1200     # Negative savings
```

#### 4. Trend Analysis

```yaml
monthly_trend:
  june_2026:
    cost:                       15200
    vs_baseline:                -0.7%
    actions:                    "Setup phase, baseline measurement"
  
  july_2026:
    cost:                       11500
    vs_baseline:                -24.8%
    actions:                    "Automation enabled, scheduled shutdown started"
  
  august_2026:
    cost:                       9100
    vs_baseline:                -40.5%
    actions:                    "Right-sizing analysis completed, 3 clusters downsized"
  
  september_2026:
    cost:                       8200
    vs_baseline:                -46.4%
    actions:                    "PTU optimized, EDA event-driven overrides activated"
```

### Reporting Frequency

**Recommended Schedule:**

| Report Type | Frequency | Audience | Use Case |
|------------|-----------|----------|----------|
| Executive Summary | Monthly (1st of month) | Finance, Management | Budget tracking, ROI justification |
| Detailed Analysis | Monthly (3rd of month) | Platform engineering, FinOps | Operational insights, optimization opportunities |
| Trend Report | Quarterly | Leadership, CFO | Strategic planning, cost forecasting |
| Ad-hoc Alert | On-demand (EDA trigger) | Operations team | Budget threshold alerts, emergency response |

### Known Limitations

Automation action counts in ROI reports reflect only the current playbook run. The audit log
is held in memory for the duration of a single run and is not persisted or read back across runs,
so standalone `generate_roi_report` executions will show zero prior actions. To track monthly
actions, either: (1) chain operations in a single playbook, or (2) implement persistent audit
log storage.

---

## Cost Calculator Template

Use this template to estimate ROI for your specific infrastructure before implementing automation.

**File location:** Create at `docs/cost_calculator_template.yml`

```yaml
---
# Azure ML Cost Optimization - ROI Calculator
# Fill in your values to estimate potential savings

project_info:
  organization: "MyOrg"
  environment: "production"
  completion_date: "2026-06-01"
  baseline_period: "Q1 2026 (Mar-May)"

# Current Infrastructure
infrastructure:
  
  # CPU Compute Clusters
  cpu_clusters:
    - name: "data-team-cpu"
      vm_size: "Standard_DS4_v2"
      hourly_rate: 0.54
      num_nodes: 4
      
    - name: "ml-team-cpu"
      vm_size: "Standard_DS5_v2"
      hourly_rate: 0.72
      num_nodes: 2
  
  # GPU Compute Clusters
  gpu_clusters:
    - name: "gpu-intensive-1"
      vm_size: "Standard_NC12s_v3"
      hourly_rate: 6.12
      num_nodes: 2
    
    - name: "gpu-intensive-2"
      vm_size: "Standard_NC6s_v3"
      hourly_rate: 3.06
      num_nodes: 4
  
  # Azure OpenAI
  openai:
    - name: "openai-east"
      ptu_capacity: 100
      monthly_cost: 5000
      utilization_percent: 45
    
    - name: "openai-west"
      ptu_capacity: 50
      monthly_cost: 2500
      utilization_percent: 55
  
  # Storage
  storage:
    monthly_cost: 500

# Operational Assumptions
assumptions:
  # What % of the month do clusters run 24/7?
  cluster_uptime_percent: 100
  
  # What % of cluster capacity is actually used for jobs?
  average_utilization_percent: 40
  
  # Implied idle time = uptime - utilization
  # 100% uptime × 40% utilization = 60% idle time

# Automation Parameters
automation_config:
  
  # Scheduled Shutdown
  shutdown:
    enabled: true
    shutdown_time: "18:00"  # 6pm
    startup_time: "08:00"   # 8am
    shutdown_days: "Mon-Fri"
    weekend_shutdown: true
    
    # Calculate hours saved
    weekday_hours_saved: 14  # 6pm-8am
    weekday_days_per_week: 5
    weekend_hours_saved: 48  # Entire weekend
    weekend_days_per_week: 2
    
    # Weeks per month
    weeks_per_month: 4.3
    
    total_hours_saved_per_month: |
      ((14 × 5) + (24 × 2)) × 4.3 = 507 hours/month
  
  # Right-Sizing
  rightsize:
    enabled: true
    cpu_threshold_percent: 30  # Downsize if avg CPU < 30%
    analysis_days: 7
    estimated_downsize_percent: 20  # Estimate % of clusters will be downsized
    avg_downsize_savings_per_hour: 0.15  # Avg hourly savings per downsized cluster
  
  # PTU Optimization
  ptu_optimization:
    enabled: true
    scale_down_threshold_percent: 50
    estimated_optimization_percent: 30  # % of PTU capacity to reduce
  
  # EDA Event-Driven
  eda:
    enabled: true
    estimated_emergency_shutdowns_per_month: 1
    avg_savings_per_event: 2000

# Cost Calculations (Automated)
# Fill in top section, these will be calculated:

monthly_baseline:
  cpu_cluster_cost: 0  # (num_nodes × hourly_rate × 730 hours)
  gpu_cluster_cost: 0  # (num_nodes × hourly_rate × 730 hours)
  openai_cost: 0       # (sum of monthly costs)
  storage_cost: 0      # (storage monthly cost)
  total_baseline: 0    # (sum of above)

monthly_post_automation:
  # After shutdown: reduce cluster hours from 730 to (730 - 507)
  cpu_cluster_hours: 223
  gpu_cluster_hours: 223
  cpu_cluster_cost: 0  # (nodes × rate × 223 hours)
  gpu_cluster_cost: 0  # (nodes × rate × 223 hours)
  
  # Right-sizing savings
  rightsize_savings: 0 # (estimated_downsize_percent × hourly_cost × 730)
  
  # PTU optimization
  openai_cost: 0       # (reduced PTU costs)
  
  # EDA savings
  eda_savings: 0       # (emergency_shutdowns × avg_savings)
  
  storage_cost: 0      # (storage - growing)
  total_cost: 0        # (sum of costs)

roi_summary:
  monthly_savings: 0   # (baseline - post_automation)
  monthly_savings_percent: 0  # (savings / baseline × 100)
  annual_savings: 0    # (monthly_savings × 12)
  payback_period_months: 0  # (implementation_cost / monthly_savings)

# Implementation Cost (One-time + Annual)
implementation:
  aap_licensing_annual: 30000
  eda_licensing_annual: 10000
  professional_services_onetime: 10000
  total_first_year: 50000
  
  payback_period_months: 0  # (first_year_cost / monthly_savings)
```

---

## Reporting Templates

### Template 1: Executive Summary Report

**Frequency:** Monthly (1st of month)  
**Audience:** Finance, Leadership, Management

```markdown
# Azure ML Platform - Cost Optimization ROI Report
**Report Date:** September 1, 2026  
**Reporting Period:** September 2026 (Month-to-Date)  
**Baseline Period:** June-August 2026 average

## Executive Summary

The Azure ML cost optimization initiative has delivered **$7,100 in monthly savings (46% reduction)** with annualized impact of **$85,200**. Key metrics show consistent optimization across compute lifecycle, right-sizing, and Azure OpenAI provisioning.

## Key Metrics

| Metric | Baseline | Current | Savings | % Change |
|--------|----------|---------|---------|----------|
| **Monthly Infrastructure Cost** | $15,300 | $8,200 | $7,100 | -46% |
| **GPU Cluster Hours** | 730 | 223 | 507 | -69% |
| **Azure OpenAI PTU** | $5,000 | $2,500 | $2,500 | -50% |
| **Projected Annual Savings** | - | - | $85,200 | - |

## Actions Taken This Month

- **23 compute cluster shutdowns** — Eliminated idle time during off-hours
- **3 GPU clusters right-sized** — Downsized underutilized clusters
- **Azure OpenAI PTU reduced** — 100 PTU → 50 PTU (low utilization detected)
- **2 EDA emergency triggers** — Prevented budget overruns

## Trend Analysis (Last 6 Months)

```
Month       | Cost   | vs Baseline | Key Action
------------|--------|-------------|---------------------------
Jun 2026    | $15,200| +1%        | Baseline measurement
Jul 2026    | $11,500| -24%       | Automation enabled
Aug 2026    | $9,100 | -40%       | Right-sizing completed
Sep 2026    | $8,200 | -46%       | PTU optimization active
```

## Cost Breakdown (Current vs Baseline)

### Compute Clusters

| Cluster Type | Baseline/Month | Current/Month | Savings | Reason |
|--------------|---|---|---|---|
| CPU (24/7 ops) | $2,365 | $724 | $1,641 | Scheduled shutdown |
| GPU (24/7 ops) | $8,935 | $2,752 | $6,183 | Scheduled shutdown |
| **Subtotal** | **$11,300** | **$3,476** | **$7,824** | - |

### Azure OpenAI

| Account | Baseline | Current | Savings | Action |
|---------|----------|---------|---------|--------|
| Primary (100 PTU) | $5,000 | $2,500 | $2,500 | Downscale to 50 PTU |
| Secondary (pay-as-you-go) | - | - | - | No change |
| **Subtotal** | **$5,000** | **$2,500** | **$2,500** | - |

### Storage

| Type | Baseline | Current | Delta | Note |
|------|----------|---------|-------|------|
| ML Datasets | $100 | $224 | -$124 | Growing (expected) |

### Summary

```
Compute savings:        $7,824 (47% of total)
OpenAI savings:         $2,500 (35% of total)
Storage increase:       -$124 (offset)
─────────────────────────────────
Total monthly savings:  $7,100
```

## ROI Investment Impact

| Category | Amount | Status |
|----------|--------|--------|
| AAP annual licensing | $30,000 | In progress |
| EDA licensing (annual) | $10,000 | In progress |
| Professional services (one-time) | $10,000 | Completed |
| **First-year cost** | **$50,000** | - |
| **Monthly savings** | **$7,100** | - |
| **Payback period** | **7.0 months** | - |
| **First-year ROI** | **41%** | - |

## Next Steps

1. **Expand right-sizing** — Additional cluster analysis for more optimization opportunities
2. **Azure Policy enforcement** — Prevent unauthorized GPU deployments
3. **Spot VM migration** — Evaluate non-critical workloads for Spot instances (estimated $2,000/month additional savings)
4. **Reserved Instance analysis** — Long-term cost reduction opportunities

---

**Report generated by:** Azure ML Cost Optimization Automation  
**Next report:** October 1, 2026
```

### Template 2: Detailed Technical Analysis

**Frequency:** Monthly (3rd of month)  
**Audience:** Platform Engineering, FinOps Team

```markdown
# Azure ML Cost Optimization - Technical Analysis Report
**Report Date:** September 3, 2026  
**Period:** September 2026

## Cluster-Level Performance

### Shutdown/Startup Analysis

**Summary:**
- Total shutdown operations: 23
- Total startup operations: 21
- Success rate: 95.7% (failed: 2 operations - cluster already stopped)
- Average time to shutdown: 8 minutes
- Average time to startup: 12 minutes

**Cluster Shutdown Events:**

| Cluster Name | Workspace | Shutdown Date | Mode | Duration | Jobs Preserved | Notes |
|--------------|-----------|---------------|------|----------|---|---|
| ds-team-a-gpu | team-a-ml-workspace | Sep 1 | graceful | 7 min | 0 | Normal schedule |
| ds-team-b-gpu | team-b-ml-workspace | Sep 1 | graceful | 8 min | 1 | Preserved running job |
| gpu-intensive-1 | research-workspace | Sep 2 | graceful | 6 min | 0 | EDA emergency trigger |

### Right-Sizing Recommendations

**Analysis Period:** August 25 - September 1, 2026  
**CPU Threshold:** 30% average utilization

| Cluster | Size | Avg CPU (7d) | Recommendation | Est. Savings/mo | Status |
|---------|------|--------------|---|---|---|
| data-team-cpu-1 | DS5_v2 | 22% | Downsize to DS4_v2 | $131 | ✓ Applied |
| data-team-cpu-2 | DS4_v2 | 18% | Downsize to DS3_v2 | $197 | ✓ Applied |
| data-team-cpu-3 | DS3_v2 | 28% | No action | - | - |
| ml-team-cpu | DS5_v2 | 45% | No action | - | - |

**Resize Validation:**
- All downsizes within `allowed_sizes` list ✓
- All downsizes above `min_size` ✓
- GPU clusters excluded from downsize analysis ✓

### Azure OpenAI PTU Analysis

**Analysis Period:** August 25 - September 1, 2026

| Account | Current PTU | Avg Utilization (7d) | Recommendation | Action | Savings |
|---------|---|---|---|---|---|
| openai-east | 100 | 45% | Scale down to 50 | ✓ Applied | $2,500/mo |
| openai-west | 50 | 55% | Maintain | - | - |

**Scale-Down Logic:**
- Threshold: Utilization < 50% for 7 consecutive days
- openai-east met criteria: 45% < 50% ✓
- New capacity: 50 PTU (sufficient for peak observed at 55% of 50 = 27.5 PTU equivalent)

## EDA Event Analysis

**Events Monitored:** Azure Cost Management (Event Grid → Service Bus)

| Event Date | Type | Trigger | Action Taken | Result |
|---|---|---|---|---|
| Sep 2, 14:30 | Budget threshold | 80% of monthly budget | Emergency shutdown (non-critical clusters) | Prevented $2,000 overrun |
| Sep 15, 09:15 | Cost anomaly | Unexpected spike | Alert sent, no action taken | Investigation ongoing |

**EDA Reliability:**
- Events detected: 2 of 2 threshold events ✓
- Rule execution success rate: 100%
- Average response time: < 2 minutes

## Error & Exception Handling

**Operations with Issues:**

| Date | Operation | Cluster | Error | Resolution |
|---|---|---|---|---|
| Sep 8 | Shutdown | gpu-intensive-2 | Timeout (30 min) | Job running, preserved per policy |
| Sep 12 | Rightsize | data-team-cpu-2 | API throttle | Retried after 15s, succeeded |

**Error Rate:** 2 errors in 44 operations = 4.5% (within acceptable range)

## Metrics Performance

**API Call Performance:**

| API Endpoint | Avg Latency | Max Latency | Error Rate |
|---|---|---|---|
| Azure Monitor (metrics) | 1.2s | 3.4s | 0% |
| Azure ML (cluster config) | 0.8s | 2.1s | 0% |
| Cost Management (current costs) | 4.5s | 12.3s | 0% |

**Audit Logging:**
- Log entries created: 44 (1 per operation)
- Log retention: 90 days
- Searchable tags: operation, timestamp, cluster, result

## Optimization Opportunities (Next Month)

### High Priority

1. **GPU Right-Sizing** — Current analysis excludes GPU clusters
   - Potential savings: $800-1200/month
   - Action: Implement GPU-specific metrics (GPU memory %, not just CPU)
   - Timeline: October 2026

2. **Spot VM Migration** — Non-critical workloads
   - Potential savings: $2,000-3,000/month
   - Action: Identify candidates, evaluate batch job workloads
   - Timeline: October 2026

### Medium Priority

3. **Reserved Instance Analysis** — Long-term commitment
   - Potential savings: 30-40% on compute (annualized)
   - Action: Analyze 12-month usage trends
   - Timeline: November 2026

---

**Report Generated:** 2026-09-03T10:15:30Z  
**Next Report:** October 3, 2026
```

### Template 3: Trend & Forecasting Report

**Frequency:** Quarterly  
**Audience:** CTO, Finance, Strategic Planning

```markdown
# Azure ML Cost Optimization - Quarterly Trend & ROI Forecast
**Report Period:** Q3 2026 (Jul-Sep 2026)  
**Reporting Date:** October 1, 2026

## Executive Overview

Three months into the automation initiative, the platform has delivered consistent cost reductions with an upward trajectory. Month-over-month improvements demonstrate the compounding value of accumulated optimizations.

## Quarterly Performance

### Cost Trend (Q3 2026)

```
Month       | Baseline | Actual | Savings | % Saved | Trend
------------|----------|--------|---------|---------|--------
July 2026   | $15,300  | $11,500| $3,800  | 25%    | ↑ Startup
August 2026 | $15,300  | $9,100 | $6,200  | 41%    | ↑ Accelerating
Sept 2026   | $15,300  | $8,200 | $7,100  | 46%    | ↑ Optimizing
────────────┼──────────┼────────┼─────────┼─────────┼─────────
Q3 Average  | $15,300  | $9,600 | $5,700  | 37%    | ✓ On target
```

### Cumulative Savings (3-Month Period)

```
July 2026:       $3,800
August 2026:     $6,200
September 2026:  $7,100
─────────────────────────
TOTAL Q3:       $17,100

Annualized Run Rate (Sep): $85,200
```

## Savings Drivers (Component Breakdown)

### Scheduled Shutdown (Dominant Driver)

**July:** $2,500 (65% of savings)
- Nightly shutdown just implemented
- Phased rollout to clusters

**August:** $4,100 (66% of savings)
- All CPU clusters on schedule
- GPU clusters added to rotation

**September:** $4,500 (63% of savings)
- Consistent execution
- Slight variance from weekend monitoring

**Quarterly Contribution:** $11,100 (65% of all savings)

### Right-Sizing (Growth Driver)

**July:** $200 (5% of savings)
- Baseline analysis phase

**August:** $1,500 (24% of savings)
- 3 clusters downsized
- Data-driven analysis process mature

**September:** $1,200 (17% of savings)
- Fewer candidates remaining
- Saturation point approaching

**Quarterly Contribution:** $2,900 (17% of all savings)

### Azure OpenAI PTU Optimization (New Driver)

**July:** $500 (13% of savings)
- Pay-as-you-go optimization only

**August:** $800 (13% of savings)
- 1 PTU account identified as candidate

**September:** $2,500 (35% of savings)
- PTU scale-down implemented
- Highest impact action in September

**Quarterly Contribution:** $3,800 (22% of all savings)

### EDA Event-Driven Actions (Emergency Driver)

**July:** $300 (8% of savings)
- 1 emergency threshold event

**August:** $0 (0% of savings)
- No threshold events

**September:** $400 (6% of savings)
- 1 anomaly detection event

**Quarterly Contribution:** $700 (4% of all savings)

## ROI Projection (6-Month & 12-Month)

### 6-Month Projection (Oct-Dec 2026)

**Assumptions:**
- September optimization level maintained (46% savings)
- Potential additional savings from new initiatives: +5%
- Total expected monthly savings: $7,200-7,500

**Projection:**

```
Oct 2026: $7,200 (conservative, post-optimization saturation)
Nov 2026: $7,200 (seasonal, potential small increase from RI analysis)
Dec 2026: $7,300 (holiday usage patterns, fewer optimizations needed)
─────────────────────
Q4 2026:  $21,700
```

### 12-Month Projection (2026 Full Year)

```
Q1 2026: $45,900 (Jun-Aug baseline, Sep partial year)
Q2 2026: $21,700 (Oct-Dec projected)
─────────────────────
TOTAL 2026: $67,600

Note: Starting June 2026, full year would have $85,200 if automation
ran full 12 months (36,400 for first 3 months + 85,200 for remaining 9 months)
```

### 2027 Projection (Full Year)

**Assumptions:**
- Current automation level maintained (46% savings = $7,100/month)
- New initiatives launched (Spot VM, Azure Policy): +10% additional savings
- Equipment refresh cycle: +5% potential optimization
- Growth in data science team: -3% (new resources, initial utilization)

**Projection:**

```
Baseline scenario (46% maintained):  $85,200/year
Growth scenario (+51% optimized):    $92,000/year
Conservative scenario (44% achieved): $80,500/year
─────────────────────────────────────────────────
EXPECTED RANGE: $80,500 - $92,000/year
BEST ESTIMATE: $85,200/year
```

## Investment Analysis

### Implementation Costs

```
Year 1 (2026):
  AAP annual licensing:     $30,000
  EDA licensing:            $10,000
  Professional services:    $10,000
  ─────────────────────────────────
  Total Year 1:            $50,000

Year 2+ (Annual):
  AAP annual licensing:     $30,000
  EDA licensing:            $10,000
  ─────────────────────────────────
  Annual recurring:        $40,000
```

### ROI Timeline

```
Month 1-7 (Payback Period):
  Cumulative savings (Jul-Jan):    $50,100
  Investment cost (Year 1):        $50,000
  ✓ Payback achieved by January 2027

Year 1 (2026) Full Year ROI:
  Savings (6 months: Jun-Dec):     $67,600
  Investment (Year 1):             $50,000
  Net benefit Year 1:              $17,600
  ROI percentage:                  35%

Year 2 (2027) Full Year ROI:
  Savings (12 months):             $85,200
  Investment (Year 2):             $40,000
  Net benefit Year 2:              $45,200
  ROI percentage:                  113%

3-Year Cumulative ROI:
  Savings (30 months):            $220,000
  Investment (3 years):            $130,000
  Net benefit:                     $90,000
  ROI percentage:                  69%
```

## Strategic Recommendations

### 1. Expand Optimization (Q4 2026)

**Action:** Implement advanced right-sizing for GPU clusters
- Current: GPU analysis limited to CPU metrics
- New: GPU memory % utilization analysis
- Estimated impact: +$800-1,200/month
- Timeline: October 2026
- Effort: Low (new metrics collection)

**Action:** Spot VM migration for non-critical workloads
- Identify batch job candidates
- Configuration & testing
- Estimated impact: +$2,000-3,000/month
- Timeline: November 2026
- Effort: Medium

### 2. Policy Enforcement (Q1 2027)

**Action:** Azure Policy for cost governance
- Prevent unauthorized GPU clusters
- Enforce cost center tagging
- Auto-shutdown of untagged resources
- Estimated impact: +$5,000-10,000/month (prevention)
- Timeline: Q1 2027
- Effort: High

### 3. Data-Driven Forecasting (Q2 2027)

**Action:** Anomaly detection and predictive analytics
- Machine learning-based cost prediction
- Proactive optimization recommendations
- Capacity planning based on trends
- Estimated impact: +$1,000-2,000/month (early detection)
- Timeline: Q2 2027
- Effort: High

## Risk Assessment

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|---|---|---|
| Unplanned cluster shutdown | Low | High | Preserve running jobs enabled by default |
| Metrics API throttling | Medium | Medium | Implement exponential backoff, cache metrics |
| EDA rule misconfiguration | Low | High | Dry-run testing before production |
| Storage cost growth | High | Low | Monitor growth, implement retention policies |

### Financial Risks

| Risk | Probability | Impact | Mitigation |
|------|---|---|---|
| Slower adoption than projected | Medium | Medium | Expand automation to additional teams |
| Azure service pricing increases | Medium | Medium | Shift to reserved instances, long-term commitments |
| Hardware refresh cycle | Low | Low | Budget refresh costs separately |

---

**Report Prepared By:** FinOps & Automation Team  
**Next Report:** January 1, 2027 (Q4 2026 results)  
**Questions?** Contact: [Cost Optimization Team]
```

---

## Additional Resources

### Baseline Establishment Checklist

- [ ] Query Azure Cost Management API for past 3 months
- [ ] Identify all ML-related resource groups and workspaces
- [ ] Calculate average monthly baseline cost
- [ ] Document infrastructure details (clusters, sizes, regions)
- [ ] Record current PTU provisioning for Azure OpenAI accounts
- [ ] Establish cost tracking dashboard or report schedule
- [ ] Set baseline variable in `cost_optimization_vars.yml`
- [ ] Configure monthly automated report generation

### ROI Tracking Best Practices

1. **Establish Single Source of Truth** — Use Cost Management API as authoritative cost data source
2. **Track from Day One** — Capture pre-automation costs for 3+ months before enabling automation
3. **Monthly Review** — Generate ROI reports on consistent schedule (1st of month recommended)
4. **Adjust Baseline Seasonally** — Account for usage patterns (more resources during peak projects)
5. **Communicate Early Wins** — Share monthly savings with stakeholders to build support
6. **Plan Investments** — Reinvest savings into additional cloud optimization initiatives
7. **Validate Assumptions** — Compare projected vs actual savings monthly and adjust forecasts

### References

- Azure Cost Management API: https://docs.microsoft.com/en-us/rest/api/cost-management/
- Azure Monitor Metrics: https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/metrics-supported
- Azure ML Compute Pricing: https://azure.microsoft.com/en-us/pricing/details/machine-learning/
- Azure OpenAI PTU Pricing: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
