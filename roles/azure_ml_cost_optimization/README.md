# azure_ml_cost_optimization

A role to optimize Azure ML/AI infrastructure costs through automated lifecycle management, event-driven overrides, and continuous right-sizing.

## Description

This role reduces Azure ML infrastructure costs by 30-50% through:
- **Scheduled compute lifecycle** - Automated shutdown/startup of ML clusters during non-business hours
- **Event-driven cost control** - EDA-triggered emergency shutdown when budgets are exceeded
- **Continuous right-sizing** - Metrics-driven downsizing of underutilized clusters
- **PTU optimization** - Azure OpenAI Provisioned Throughput Unit management
- **ROI tracking** - Automated savings reports vs baseline costs

## Requirements

- Ansible >= 2.14.0
- azure.azcollection collection
- Azure subscription with:
  - Contributor role (for resource modifications)
  - Monitoring Reader role (for metrics access)
  - Cost Management Reader role (for cost data)

## Role Variables

### Core Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_operation` | string | Yes | `""` | Operation to perform: `shutdown_compute`, `startup_compute`, `analyze_and_rightsize`, `manage_ptu`, `generate_roi_report` |
| `azure_resource_group` | string | Yes | - | Azure resource group containing ML resources |
| `azure_region` | string | Yes | - | Azure region |

### Target Resources

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_workspaces` | list | No | `[]` | Filter specific ML workspaces (empty = all) |
| `azure_ml_cost_optimization_compute_targets` | list | No | `[]` | Filter specific compute clusters (empty = all) |
| `azure_ml_cost_optimization_openai_accounts` | list | No | `[]` | Filter specific OpenAI accounts (empty = all) |

### Shutdown/Startup Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_shutdown_mode` | string | No | `graceful` | `graceful` (wait for jobs) or `immediate` |
| `azure_ml_cost_optimization_preserve_running_jobs` | boolean | No | `true` | Skip clusters with active jobs during shutdown |

### Right-Sizing Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_rightsize_enabled` | boolean | No | `true` | Enable right-sizing analysis |
| `azure_ml_cost_optimization_rightsize_cpu_threshold` | integer | No | `30` | CPU % threshold for downsizing |
| `azure_ml_cost_optimization_rightsize_analysis_days` | integer | No | `7` | Days of metrics to analyze |
| `azure_ml_cost_optimization_rightsize_allowed_sizes` | list | No | `[Standard_DS3_v2, Standard_DS4_v2, Standard_DS5_v2]` | VM sizes allowed for auto-resize |
| `azure_ml_cost_optimization_rightsize_min_size` | string | No | `Standard_DS3_v2` | Never downsize below this |

### PTU Management Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_ptu_target_utilization` | integer | No | `80` | Target PTU utilization % |
| `azure_ml_cost_optimization_ptu_scale_down_threshold` | integer | No | `50` | Scale down if utilization below this |

### Event-Driven Ansible (EDA) Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_emergency_mode` | boolean | No | `false` | Trigger emergency shutdown mode (all non-essential compute) |
| `azure_ml_cost_optimization_budget_alert_action` | string | No | `shutdown_non_critical` | `shutdown_all`, `shutdown_non_critical`, or `alert_only` |

### ROI Tracking Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_roi_baseline_monthly_cost` | integer | Yes (for ROI report) | `0` | Baseline monthly cost (USD) before automation |
| `azure_ml_cost_optimization_roi_tracking_start_date` | string | No | `""` | ISO 8601 date when automation started |
| `azure_ml_cost_optimization_roi_report_path` | string | No | `/tmp/roi_report_{{ ansible_date_time.date }}.md` | Output path for ROI report |

### Audit Logging Configuration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `azure_ml_cost_optimization_enable_audit_log` | boolean | No | `false` | Enable detailed audit logging |
| `azure_ml_cost_optimization_audit_log_path` | string | No | `/tmp/azure_ml_cost_optimization_{{ ansible_date_time.date }}.yml` | Path for audit log output |

## Dependencies

None.

## Operations

The role supports five core operations, specified via the `azure_ml_cost_optimization_operation` variable:

### shutdown_compute

Gracefully or immediately shuts down Azure ML compute clusters and scales down Azure OpenAI PTU.

**Key Features:**
- Supports graceful shutdown (waits for running jobs) or immediate mode
- Can preserve clusters with active jobs to prevent disruption
- Scales down Azure OpenAI PTU allocation
- Idempotent (safe to run repeatedly)

**Expected Output:**
- Clusters transitioned to stopped state
- PTU scaled down to minimum allocation
- Audit log entry if enabled
- Skipped summary if preserve_running_jobs is enabled

### startup_compute

Starts Azure ML compute clusters and restores Azure OpenAI PTU allocation.

**Key Features:**
- Restores clusters to operational state
- Scales PTU back to configured minimum
- Configurable minimum node count for cluster auto-scaling
- Idempotent (already-running clusters unchanged)

**Expected Output:**
- Clusters transitioned to running state
- PTU scaled to target allocation
- Ready for compute jobs
- Audit log entry if enabled

### analyze_and_rightsize

Analyzes Azure Monitor metrics and automatically downsizes underutilized clusters.

**Key Features:**
- Collects CPU/GPU utilization metrics for specified analysis period
- Compares against configured CPU threshold
- Proposes downsizing for persistently underutilized clusters
- Never upsizes clusters or goes below minimum configured size
- Respects whitelist of allowed VM sizes

**Key Thresholds:**
- CPU threshold: Default 30% (clusters below this are candidates for downsizing)
- Analysis period: Default 7 days
- Never downsizes below `Standard_DS3_v2` or configured minimum

**Expected Output:**
- Right-sizing recommendations with projected savings
- VM size change candidates identified
- Applied size changes (if auto-apply enabled)
- Utilization metrics for each cluster analyzed
- Audit log entry if enabled

### manage_ptu

Manages Azure OpenAI Provisioned Throughput Unit (PTU) allocation based on actual usage patterns.

**Key Features:**
- Analyzes current PTU utilization
- Scales down if utilization below configured threshold
- Scales up if utilization approaches target
- Optimizes cost without service degradation
- Prevents overprovisioning

**Key Thresholds:**
- Target utilization: Default 80% (aims to operate at this level)
- Scale-down threshold: Default 50% (scales down if below this)
- Scale-up threshold: Dynamic based on target

**Expected Output:**
- Current PTU utilization metrics
- Scale action taken (up/down/none)
- Projected cost savings
- PTU audit trail
- Audit log entry if enabled

### generate_roi_report

Generates comprehensive cost optimization ROI report.

**Key Features:**
- Compares current costs against baseline
- Calculates total savings to date
- Projects annual savings
- Lists all optimization actions taken
- Generates markdown report for stakeholder review

**Report Includes:**
- Baseline vs current costs
- Total savings (USD and percentage)
- Projected annual savings
- Cost breakdown by operation type
- List of actions taken during tracking period
- Recommendations

**Expected Output:**
- Markdown report file at configured path
- Report summary printed to stdout
- Ready for stakeholder communication

## Example Playbooks

### Shutdown Compute Clusters

```yaml
- hosts: localhost
  tasks:
    - name: Shutdown ML compute clusters
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: shutdown_compute
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_shutdown_mode: graceful
        azure_ml_cost_optimization_preserve_running_jobs: true
```

**Expected Output:**
```
TASK [Shutdown ML compute clusters]
ok: [localhost] => {
  "msg": "Successfully shut down 3 compute clusters"
}
```

### Startup Compute Clusters

```yaml
- hosts: localhost
  tasks:
    - name: Startup ML compute clusters
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: startup_compute
        azure_resource_group: ml-platform-prod
        azure_region: eastus
```

**Expected Output:**
```
TASK [Startup ML compute clusters]
ok: [localhost] => {
  "msg": "Successfully started 3 compute clusters"
}
```

### Right-Size Underutilized Clusters

```yaml
- hosts: localhost
  tasks:
    - name: Analyze and rightsize clusters
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: analyze_and_rightsize
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_rightsize_cpu_threshold: 30
        azure_ml_cost_optimization_rightsize_analysis_days: 7
```

**Expected Output:**
```
TASK [Analyze and rightsize clusters]
ok: [localhost] => {
  "results": [
    {
      "cluster_name": "training-cluster-1",
      "current_size": "Standard_DS4_v2",
      "recommended_size": "Standard_DS3_v2",
      "avg_cpu_utilization": 18,
      "projected_monthly_savings": 450
    }
  ]
}
```

### Optimize Azure OpenAI PTU

```yaml
- hosts: localhost
  tasks:
    - name: Manage Azure OpenAI PTU
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: manage_ptu
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_ptu_scale_down_threshold: 50
```

**Expected Output:**
```
TASK [Manage Azure OpenAI PTU]
ok: [localhost] => {
  "ptu_updates": [
    {
      "account_name": "prod-openai-account",
      "current_ptu": 500,
      "recommended_ptu": 350,
      "utilization": 42,
      "action": "scaled_down",
      "projected_monthly_savings": 2400
    }
  ]
}
```

### Generate ROI Report

```yaml
- hosts: localhost
  tasks:
    - name: Generate cost savings report
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: generate_roi_report
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_roi_baseline_monthly_cost: 15000
        azure_ml_cost_optimization_roi_report_path: /tmp/roi_report.md
```

**Expected Output:**
```
TASK [Generate cost savings report]
ok: [localhost] => {
  "report_generated": true,
  "report_path": "/tmp/roi_report.md",
  "summary": {
    "baseline_monthly_cost": 15000,
    "current_monthly_cost": 10200,
    "total_savings": 4800,
    "savings_percentage": 32,
    "projected_annual_savings": 57600
  }
}
```

## Advanced Usage

### Scoped Operations

Restrict operations to specific workspaces or compute targets:

```yaml
- hosts: localhost
  tasks:
    - name: Shutdown only production compute
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: shutdown_compute
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_workspaces:
          - prod-workspace-1
          - prod-workspace-2
        azure_ml_cost_optimization_compute_targets:
          - production-training-cluster
```

### Emergency Budget Override (EDA Integration)

Trigger emergency shutdown when budget is exceeded:

```yaml
- hosts: localhost
  tasks:
    - name: Emergency shutdown (budget exceeded)
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: shutdown_compute
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_emergency_mode: true
        azure_ml_cost_optimization_shutdown_mode: immediate
        azure_ml_cost_optimization_preserve_running_jobs: false
        azure_ml_cost_optimization_budget_alert_action: shutdown_non_critical
```

### With Audit Logging

Enable detailed audit trail for compliance:

```yaml
- hosts: localhost
  tasks:
    - name: Shutdown with audit logging
      ansible.builtin.include_role:
        name: cloud.azure_ops.azure_ml_cost_optimization
      vars:
        azure_ml_cost_optimization_operation: shutdown_compute
        azure_resource_group: ml-platform-prod
        azure_region: eastus
        azure_ml_cost_optimization_enable_audit_log: true
        azure_ml_cost_optimization_audit_log_path: /var/log/ml_cost_optimization.yml
```

## Ansible Automation Platform Integration

### Scheduled Lifecycle Management

Create a workflow template with two scheduled jobs:

**Evening Shutdown (6pm, weekdays):**
```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=shutdown_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_shutdown_mode=graceful
```

**Morning Startup (8am, weekdays):**
```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=startup_compute \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus
```

**Weekly Right-Sizing (Monday 2am):**
```bash
ansible-playbook playbooks/cost_optimization.yml \
  -e operation=analyze_and_rightsize \
  -e azure_resource_group=ml-platform-prod \
  -e azure_region=eastus \
  -e azure_ml_cost_optimization_rightsize_analysis_days=7
```

### Event-Driven Ansible Integration

EDA rulebook example for budget-threshold events:

```yaml
---
- name: Handle Azure cost alert
  hosts: all
  sources:
    - name: azure_cost_events
      plugin: ansible.eda.azure_event_grid
      args:
        connection_string: "{{ eda_azure_connection }}"
        topic_name: cost_alerts

  rules:
    - name: Budget exceeded - emergency shutdown
      condition: event.data.event_type == "budgetAlertTriggered"
      action:
        run_playbook:
          name: playbooks/cost_optimization.yml
          extra_vars:
            operation: shutdown_compute
            azure_ml_cost_optimization_emergency_mode: true
            azure_ml_cost_optimization_shutdown_mode: immediate
            azure_ml_cost_optimization_preserve_running_jobs: false
```

## Testing

### Test Prerequisites

Before running tests, ensure:
1. Azure CLI is configured: `az account show`
2. Service Principal has required roles (Contributor, Monitoring Reader, Cost Management Reader)
3. Target resource group exists and contains Azure ML workspaces
4. Azure ML workspaces have compute clusters

### Manual Testing

```bash
# Test shutdown with graceful mode
ansible-playbook test_playbook.yml \
  -e azure_ml_cost_optimization_operation=shutdown_compute \
  -e azure_ml_cost_optimization_shutdown_mode=graceful \
  -e azure_resource_group=test-rg

# Test startup
ansible-playbook test_playbook.yml \
  -e azure_ml_cost_optimization_operation=startup_compute \
  -e azure_resource_group=test-rg

# Test right-sizing analysis
ansible-playbook test_playbook.yml \
  -e azure_ml_cost_optimization_operation=analyze_and_rightsize \
  -e azure_ml_cost_optimization_rightsize_cpu_threshold=25 \
  -e azure_resource_group=test-rg

# Test ROI report generation
ansible-playbook test_playbook.yml \
  -e azure_ml_cost_optimization_operation=generate_roi_report \
  -e azure_ml_cost_optimization_roi_baseline_monthly_cost=10000 \
  -e azure_resource_group=test-rg
```

### Idempotency Verification

All operations are idempotent. Test by running the same operation twice:

```bash
# First run
ansible-playbook test_playbook.yml \
  -e azure_ml_cost_optimization_operation=shutdown_compute \
  -e azure_resource_group=test-rg

# Second run - should be idempotent (no changes)
ansible-playbook test_playbook.yml \
  -e azure_ml_cost_optimization_operation=shutdown_compute \
  -e azure_resource_group=test-rg
```

Expected behavior: Both runs complete successfully with unchanged status on the second run.

## Troubleshooting

### Issue: "Module not found: azure.azcollection"

**Solution:** Install the required collection
```bash
ansible-galaxy collection install azure.azcollection
```

### Issue: Authentication fails with "Invalid credentials"

**Troubleshooting:**
1. Verify Azure CLI authentication: `az account show`
2. Ensure service principal has required roles
3. Check that `AZURE_SUBSCRIPTION_ID` and `AZURE_CLIENT_*` variables are set

**Solution:**
```bash
# Authenticate with Azure CLI
az login

# Or set service principal environment variables
export AZURE_CLIENT_ID=your-client-id
export AZURE_CLIENT_SECRET=your-client-secret
export AZURE_TENANT_ID=your-tenant-id
export AZURE_SUBSCRIPTION_ID=your-subscription-id
```

### Issue: Operation times out when collecting metrics

**Troubleshooting:**
1. Check Azure Monitor API availability
2. Verify resource group has compute clusters
3. Increase analysis period if timeouts persist

**Solution:**
```yaml
# Increase analysis period to reduce data collection time
azure_ml_cost_optimization_rightsize_analysis_days: 3
```

### Issue: Right-sizing recommendations not generated

**Troubleshooting:**
1. Verify `azure_ml_cost_optimization_rightsize_enabled: true`
2. Check that analysis period has sufficient metric data (min 7 days)
3. Ensure clusters have CPU metrics available in Azure Monitor
4. Verify clusters are in specified resource group

**Solution:**
- Wait for metrics to accumulate (7 days minimum)
- Check cluster metrics in Azure Portal > Monitor
- Verify resource group and workspace filters are correct

### Issue: ROI report shows zero savings

**Troubleshooting:**
1. Verify baseline cost is set correctly
2. Check that `azure_ml_cost_optimization_roi_tracking_start_date` is in the past
3. Ensure cost data has time to aggregate in Azure Cost Management

**Solution:**
```yaml
# Set baseline to actual current cost
azure_ml_cost_optimization_roi_baseline_monthly_cost: 15000

# Set tracking start date to when automation began
azure_ml_cost_optimization_roi_tracking_start_date: "2026-09-01"
```

### Issue: PTU scaling fails with "Quota exceeded"

**Troubleshooting:**
1. Check current PTU allocation vs subscription limit
2. Request PTU quota increase if at limit
3. Verify OpenAI account has capacity for scaling

**Solution:**
- Contact Azure support to increase PTU quota
- Or adjust `azure_ml_cost_optimization_ptu_target_utilization` to lower target
- Manually scale PTU in Azure Portal as interim measure

## License

GNU General Public License v3.0 or later

See [LICENSE](https://github.com/redhat-cop/cloud.azure_ops/blob/main/LICENSE) to see the full text.

## Author

Red Hat
