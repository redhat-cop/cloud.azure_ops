# AAP Workflow Templates - Azure ML Cost Optimization

This guide provides step-by-step instructions for configuring Ansible Automation Platform (AAP) workflow templates for Azure ML cost optimization operations.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Workflow Template 1: Nightly Shutdown](#workflow-template-1-nightly-shutdown)
4. [Workflow Template 2: Morning Startup](#workflow-template-2-morning-startup)
5. [Workflow Template 3: Weekly Right-Sizing](#workflow-template-3-weekly-right-sizing)
6. [Workflow Template 4: PTU Management](#workflow-template-4-ptu-management)
7. [Workflow Template 5: Monthly ROI Report](#workflow-template-5-monthly-roi-report)
8. [Scheduling Configuration](#scheduling-configuration)
9. [Testing & Validation](#testing--validation)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This solution uses 5 workflow templates to implement the cost optimization strategy:

| Template | Schedule | Purpose | Frequency |
|----------|----------|---------|-----------|
| Nightly Shutdown | 6pm weekdays | Stop idle clusters during off-hours | Daily |
| Morning Startup | 8am weekdays | Restart clusters for business hours | Daily |
| Right-Sizing Analysis | 2am Sunday | Analyze utilization and downsize | Weekly |
| PTU Management | Every hour | Optimize Azure OpenAI provisioning | Hourly |
| ROI Report | 9am 1st of month | Generate cost savings report | Monthly |

---

## Prerequisites

### Required AAP Version
- **Ansible Automation Platform 2.4+** (supports event-driven automation)

### Required Credentials
- **Azure Service Principal** with roles:
  - `Contributor` (for shutdown/startup operations)
  - `Monitoring Reader` (for metrics analysis)
  - `Cost Management Reader` (for ROI reporting)
- **Credential Type:** `Microsoft Azure Resource Manager`

### Required Project
- Project cloned from `cloud.azure_ops` collection
- Contains playbook: `cost_optimization.yml`

### Required Variables
Set these as **Extra Variables** in job templates:
```yaml
# All operations require:
operation: "shutdown_compute"  # or startup_compute, analyze_and_rightsize, manage_ptu, generate_roi_report
azure_resource_group: "ml-platform-prod"  # Your target resource group
azure_region: "eastus"  # Your Azure region
```

---

## Workflow Template 1: Nightly Shutdown

**Purpose:** Shut down ML compute clusters at end of business day to eliminate idle costs.

**Schedule:** 6:00pm (18:00) weekdays (Mon-Fri)

### Step 1: Create Job Template

1. Navigate to **Resources** → **Templates** → **Create template** → **Job template**

2. Enter details:
   - **Name:** `Cost Optimization - Shutdown Compute`
   - **Description:** Gracefully shutdown Azure ML compute clusters to reduce idle costs
   - **Organization:** Default
   - **Inventory:** `localhost`
   - **Project:** `cloud.azure_ops` (or your imported project)
   - **Playbook:** `cost_optimization.yml`
   - **Credentials:** 
     - Type: `Microsoft Azure Resource Manager`
     - Select your Azure Service Principal credential
   - **Execution Environment:** Use default (or `ee-cloud-azure` if custom EE available)

3. Scroll down to **Variables** section and enter:
   ```yaml
   operation: shutdown_compute
   azure_region: "eastus"
   ```

4. Click **Save**

### Step 2: Create Survey

1. In the job template, scroll to **Survey** section
2. Toggle **Survey enabled** to ON
3. Click **Add question**

4. **Question 1: Resource Group**
   - **Question name:** Resource Group
   - **Description:** Azure resource group containing ML resources
   - **Answer type:** Text
   - **Variable name:** `azure_resource_group`
   - **Required:** Yes
   - **Default answer:** `ml-platform-prod`
   - Click **Add**

5. **Question 2: Shutdown Mode**
   - **Question name:** Shutdown Mode
   - **Description:** How should clusters be shutdown?
   - **Answer type:** Multiple Choice
   - **Variable name:** `shutdown_mode`
   - **Multiple choice options:**
     ```
     graceful (wait for jobs, max 30 min)
     immediate (may interrupt jobs)
     ```
   - **Default answer:** `graceful`
   - **Required:** Yes
   - Click **Add**

6. **Question 3: Preserve Running Jobs**
   - **Question name:** Preserve Running Jobs
   - **Description:** Skip clusters with active jobs?
   - **Answer type:** Multiple Choice
   - **Variable name:** `preserve_running_jobs`
   - **Multiple choice options:**
     ```
     true (skip clusters with active jobs)
     false (shutdown all clusters)
     ```
   - **Default answer:** `true`
   - **Required:** Yes
   - Click **Add**

7. Click **Save survey**

### Step 3: Create Workflow Template (Optional)

For more complex orchestration, wrap in a workflow template:

1. Navigate to **Resources** → **Templates** → **Create template** → **Workflow template**

2. Enter details:
   - **Name:** `ML Cost Optimization - Nightly Shutdown`
   - **Description:** Daily shutdown of idle GPU and compute clusters
   - **Organization:** Default

3. Click **Save**

4. In the workflow editor:
   - Click **Add node** (top-left)
   - Select job template: `Cost Optimization - Shutdown Compute`
   - Configure survey answers (or leave for runtime survey)
   - Click **Save**

### Step 4: Schedule Execution

1. In the workflow template, scroll to **Schedules** section
2. Click **Add schedule**

3. Configure schedule:
   - **Name:** `Nightly Shutdown - Weekdays`
   - **Description:** Shutdown clusters at 6pm on weekdays (Mon-Fri)
   - **Schedule type:** Regular schedule
   - **Frequency:** Daily
   - **Days of Week:** 
     - Check: Monday, Tuesday, Wednesday, Thursday, Friday
     - Uncheck: Saturday, Sunday
   - **Time:** 18:00 (6pm)
   - **Time Zone:** Select your timezone (e.g., America/New_York)

4. Optionally, configure:
   - **Run on:** Specify AAP controller node
   - **Limit:** `localhost` (already set)

5. Click **Save**

### Example: Using the Template

**Manual Execution (One-time):**
```bash
# From command-line (if enabled)
awx-cli launch --template "Cost Optimization - Shutdown Compute" \
  --extra-vars '{"azure_resource_group":"ml-platform-prod"}'
```

**Scheduled Execution:**
- Runs automatically at 6pm every weekday
- Survey prompts for resource group and options
- Job logs all shutdown operations

---

## Workflow Template 2: Morning Startup

**Purpose:** Start previously-shutdown clusters to prepare for business hours.

**Schedule:** 8:00am (08:00) weekdays (Mon-Fri)

### Step 1: Create Job Template

1. Navigate to **Resources** → **Templates** → **Create template** → **Job template**

2. Enter details:
   - **Name:** `Cost Optimization - Startup Compute`
   - **Description:** Start Azure ML compute clusters for business hours
   - **Organization:** Default
   - **Inventory:** `localhost`
   - **Project:** `cloud.azure_ops`
   - **Playbook:** `cost_optimization.yml`
   - **Credentials:** Azure Service Principal
   - **Variables:**
     ```yaml
     operation: startup_compute
     azure_region: "eastus"
     ```

3. Click **Save**

### Step 2: Create Survey

1. Toggle **Survey enabled** to ON
2. Click **Add question**

3. **Question 1: Resource Group**
   - **Question name:** Resource Group
   - **Description:** Azure resource group containing ML resources
   - **Answer type:** Text
   - **Variable name:** `azure_resource_group`
   - **Required:** Yes
   - **Default answer:** `ml-platform-prod`

4. **Question 2: Specific Clusters (Optional)**
   - **Question name:** Specific Clusters to Start
   - **Description:** Comma-separated cluster names (blank = all clusters)
   - **Answer type:** Text
   - **Variable name:** `azure_ml_cost_optimization_compute_targets`
   - **Required:** No
   - **Default answer:** (blank)

5. Click **Save survey**

### Step 3: Schedule Execution

1. Scroll to **Schedules** section
2. Click **Add schedule**

3. Configure:
   - **Name:** `Morning Startup - Weekdays`
   - **Description:** Start clusters at 8am on weekdays (Mon-Fri)
   - **Frequency:** Daily
   - **Days of Week:** Monday - Friday
   - **Time:** 08:00 (8am)
   - **Time Zone:** Select your timezone

4. Click **Save**

---

## Workflow Template 3: Weekly Right-Sizing

**Purpose:** Analyze utilization metrics and automatically downsize underutilized clusters.

**Schedule:** 2:00am (02:00) Sundays

### Step 1: Create Job Template

1. Navigate to **Resources** → **Templates** → **Create template** → **Job template**

2. Enter details:
   - **Name:** `Cost Optimization - Right-Sizing Analysis`
   - **Description:** Weekly analysis of cluster utilization and right-sizing recommendations
   - **Organization:** Default
   - **Inventory:** `localhost`
   - **Project:** `cloud.azure_ops`
   - **Playbook:** `cost_optimization.yml`
   - **Credentials:** Azure Service Principal (must include Monitoring Reader role)
   - **Variables:**
     ```yaml
     operation: analyze_and_rightsize
     azure_region: "eastus"
     ```

3. Click **Save**

### Step 2: Create Survey

1. Toggle **Survey enabled** to ON
2. Click **Add question**

3. **Question 1: Resource Group**
   - **Question name:** Resource Group
   - **Description:** Azure resource group to analyze
   - **Answer type:** Text
   - **Variable name:** `azure_resource_group`
   - **Required:** Yes
   - **Default answer:** `ml-platform-prod`

4. **Question 2: CPU Utilization Threshold**
   - **Question name:** CPU Utilization Threshold
   - **Description:** CPU threshold % for identifying underutilized clusters
   - **Answer type:** Multiple Choice
   - **Variable name:** `rightsize_cpu_threshold`
   - **Multiple choice options:**
     ```
     20 (aggressive downsizing)
     30 (recommended)
     40 (conservative)
     ```
   - **Default answer:** `30`
   - **Required:** Yes

5. **Question 3: Analysis Window**
   - **Question name:** Analysis Window
   - **Description:** Number of days of metrics to analyze
   - **Answer type:** Multiple Choice
   - **Variable name:** `rightsize_analysis_days`
   - **Multiple choice options:**
     ```
     7 (recommended)
     14 (conservative)
     ```
   - **Default answer:** `7`
   - **Required:** Yes

6. Click **Save survey**

### Step 3: Schedule Execution

1. Scroll to **Schedules** section
2. Click **Add schedule**

3. Configure:
   - **Name:** `Weekly Right-Sizing Analysis`
   - **Description:** Sunday 2am analysis and right-sizing
   - **Frequency:** Weekly
   - **Days of Week:** Sunday only
   - **Time:** 02:00 (2am)
   - **Time Zone:** Select your timezone

4. Click **Save**

---

## Workflow Template 4: PTU Management

**Purpose:** Optimize Azure OpenAI Provisioned Throughput Units based on utilization.

**Schedule:** Hourly

### Step 1: Create Job Template

1. Navigate to **Resources** → **Templates** → **Create template** → **Job template**

2. Enter details:
   - **Name:** `Cost Optimization - PTU Management`
   - **Description:** Hourly optimization of Azure OpenAI Provisioned Throughput Units
   - **Organization:** Default
   - **Inventory:** `localhost`
   - **Project:** `cloud.azure_ops`
   - **Playbook:** `cost_optimization.yml`
   - **Credentials:** Azure Service Principal (must include Monitoring Reader role)
   - **Variables:**
     ```yaml
     operation: manage_ptu
     azure_region: "eastus"
     ```

3. Click **Save**

### Step 2: Create Survey

1. Toggle **Survey enabled** to ON
2. Click **Add question**

3. **Question 1: Resource Group**
   - **Question name:** Resource Group
   - **Description:** Azure resource group containing OpenAI accounts
   - **Answer type:** Text
   - **Variable name:** `azure_resource_group`
   - **Required:** Yes
   - **Default answer:** `ml-platform-prod`

4. **Question 2: Specific OpenAI Accounts (Optional)**
   - **Question name:** Specific OpenAI Accounts
   - **Description:** Comma-separated account names (blank = all accounts)
   - **Answer type:** Text
   - **Variable name:** `openai_accounts`
   - **Required:** No
   - **Default answer:** (blank)

5. Click **Save survey**

### Step 3: Schedule Execution

1. Scroll to **Schedules** section
2. Click **Add schedule**

3. Configure:
   - **Name:** `Hourly PTU Optimization`
   - **Description:** Hourly check and optimization of PTU utilization
   - **Frequency:** Daily
   - **Days of Week:** Every day (Mon-Sun)
   - **Time:** 00:00 (midnight)
   - **Interval:** Repeat every 1 hour
   - **Time Zone:** Select your timezone

4. Click **Save**

---

## Workflow Template 5: Monthly ROI Report

**Purpose:** Generate monthly cost optimization ROI report.

**Schedule:** 1st of month at 9am

### Step 1: Create Job Template

1. Navigate to **Resources** → **Templates** → **Create template** → **Job template**

2. Enter details:
   - **Name:** `Cost Optimization - ROI Report`
   - **Description:** Monthly ROI report and cost savings analysis
   - **Organization:** Default
   - **Inventory:** `localhost`
   - **Project:** `cloud.azure_ops`
   - **Playbook:** `cost_optimization.yml`
   - **Credentials:** Azure Service Principal (must include Cost Management Reader role)
   - **Variables:**
     ```yaml
     operation: generate_roi_report
     azure_region: "eastus"
     ```

3. Click **Save**

### Step 2: Create Survey

1. Toggle **Survey enabled** to ON
2. Click **Add question**

3. **Question 1: Resource Group**
   - **Question name:** Resource Group
   - **Description:** Azure resource group to report on
   - **Answer type:** Text
   - **Variable name:** `azure_resource_group`
   - **Required:** Yes
   - **Default answer:** `ml-platform-prod`

4. **Question 2: Report Output Path (Optional)**
   - **Question name:** Report Output Path
   - **Description:** File path for report output
   - **Answer type:** Text
   - **Variable name:** `report_output_path`
   - **Required:** No
   - **Default answer:** `/tmp/roi_report_{{ ansible_date_time.date }}.md`

5. **Question 3: Baseline Monthly Cost**
   - **Question name:** Baseline Monthly Cost (USD)
   - **Description:** Pre-automation monthly cost baseline for ROI calculation
   - **Answer type:** Text
   - **Variable name:** `azure_ml_cost_optimization_roi_baseline_monthly_cost`
   - **Required:** Yes
   - **Default answer:** `15300` (example)

6. Click **Save survey**

### Step 3: Schedule Execution

1. Scroll to **Schedules** section
2. Click **Add schedule**

3. Configure:
   - **Name:** `Monthly ROI Report`
   - **Description:** Generate ROI report on 1st of month at 9am
   - **Frequency:** Monthly
   - **Day of Month:** 1st
   - **Time:** 09:00 (9am)
   - **Time Zone:** Select your timezone

4. Click **Save**

### Step 4: Notifications (Optional)

Configure email or webhook notifications:

1. In job template, scroll to **Notifications** section
2. Click **Add notification template**
3. Select notification type:
   - **Email:** Send report to team
   - **Webhook:** POST report to Slack/Teams
   - **Splunk:** Forward results to Splunk

---

## Scheduling Configuration

### Cron Expression Reference

If using direct cron scheduling (advanced):

```
# Shutdown (6pm weekdays)
0 18 * * 1-5

# Startup (8am weekdays)
0 8 * * 1-5

# Right-sizing (2am Sunday)
0 2 * * 0

# PTU Management (every hour)
0 * * * *

# ROI Report (9am on 1st of month)
0 9 1 * *
```

### Time Zone Handling

When configuring schedules:
1. All times are relative to **AAP controller server time**
2. To verify timezone:
   ```bash
   # On AAP controller
   timedatectl status
   ```
3. Adjust schedule times accordingly if controller is in different timezone

### Business Hours Examples

**Example 1: US Eastern Time (5 business days)**
- Shutdown: 6pm ET (18:00)
- Startup: 8am ET (08:00)
- Days: Mon-Fri

**Example 2: Europe Central Time (5 business days)**
- Shutdown: 7pm CET (19:00)
- Startup: 7am CET (07:00)
- Days: Mon-Fri

**Example 3: Global Multi-Region**
- Create separate schedules for each region
- East US: Shutdown 6pm ET, Startup 8am ET
- West EU: Shutdown 6pm CET, Startup 8am CET

---

## Testing & Validation

### Step 1: Test Survey Variables

1. Open job template: `Cost Optimization - Shutdown Compute`
2. Click **Launch** (run template)
3. Survey appears - verify:
   - [ ] Resource Group field appears and required
   - [ ] Shutdown Mode choices are correct (graceful/immediate)
   - [ ] Preserve Running Jobs choices are correct (true/false)
   - [ ] Default values are populated correctly

4. Enter test values:
   - Resource Group: `ml-platform-prod`
   - Shutdown Mode: `graceful`
   - Preserve Running Jobs: `true`

5. Click **Next** → **Launch job**

### Step 2: Verify Execution

1. Monitor job execution in **Jobs** section
2. Check job output for:
   - Azure authentication success
   - Resource group found
   - Clusters discovered and shut down
   - Summary report with shutdown count

3. Example successful output:
   ```
   TASK [Shutdown compute clusters summary]
   ok: [localhost] => 
     msg: |
       Shutdown complete:
       - Clusters stopped: 3
       - Clusters skipped: 1 (active jobs)
       - Total cost savings: $12.50/hour
   ```

### Step 3: Test Scheduling

1. Create a test schedule set 5 minutes in the future:
   - **Frequency:** One-time (if available)
   - **Time:** 5 minutes from now

2. Wait for execution and verify:
   - [ ] Job launches automatically
   - [ ] Survey is populated (or uses defaults)
   - [ ] Execution completes successfully
   - [ ] Job appears in history

### Step 4: Test Schedule Syntax

1. Verify each scheduled template:
   ```bash
   # From AAP UI, hover over schedule name to see next execution times
   ```

2. Check AAP logs:
   ```bash
   # On AAP controller
   tail -f /var/log/awx/dispatcher.log
   
   # Should see: "Scheduled job execution started: Cost Optimization - Shutdown Compute"
   ```

### Step 5: Dry-run Testing

Before production deployment, test in check mode:

1. Modify job template extra variables:
   ```yaml
   operation: shutdown_compute
   azure_resource_group: "test-rg"  # Use test resource group
   ```

2. Launch with `--check` flag:
   ```bash
   # In playbook, add check mode
   ansible-playbook cost_optimization.yml --check \
     -e operation=shutdown_compute \
     -e azure_resource_group=test-rg
   ```

3. Verify:
   - [ ] No actual resources are modified
   - [ ] All validations pass
   - [ ] Plan shows what would change

---

## Troubleshooting

### Issue 1: "Microsoft Azure Resource Manager" Credential Not Available

**Symptom:** Cannot select Azure credential in job template

**Solution:**
1. Navigate to **Resources** → **Credentials**
2. Click **Create credential**
3. Select **Credential Type:** `Microsoft Azure Resource Manager`
4. Fill in:
   - **Name:** `Azure Service Principal - ML Platform`
   - **Description:** Service principal with Contributor + Monitoring Reader roles
   - **Client ID:** (from service principal)
   - **Client Secret:** (from service principal)
   - **Tenant ID:** (from Azure subscription)
   - **Subscription ID:** (from Azure subscription)
5. Click **Save**

### Issue 2: Survey Not Showing at Launch

**Symptom:** Click Launch but no survey questions appear

**Solution:**
1. Go back to job template
2. Scroll down to **Survey** section
3. Verify **Survey enabled** is toggled **ON**
4. Click **Save**
5. Re-launch job template

### Issue 3: Scheduled Job Never Executes

**Symptom:** Job does not run at scheduled time

**Solution:**
1. Verify schedule is **enabled** (toggle in schedule settings)
2. Check **Next Run** time shows correct future time
3. Verify **AAP Scheduler Service** is running:
   ```bash
   # On AAP controller
   systemctl status awx-dispatcher
   systemctl status awx-scheduler
   ```
4. Check logs:
   ```bash
   tail -f /var/log/awx/scheduler.log
   tail -f /var/log/awx/dispatcher.log
   ```

### Issue 4: "Insufficient Permissions" Error

**Symptom:** Job fails with Azure permission error

**Solution:**
1. Verify service principal has correct roles:
   ```bash
   az role assignment list \
     --assignee <service-principal-id> \
     --subscription <subscription-id>
   ```
2. Expected roles:
   - `Contributor` (for shutdown/startup)
   - `Monitoring Reader` (for metrics)
   - `Cost Management Reader` (for ROI report)
3. Add missing roles:
   ```bash
   az role assignment create \
     --assignee <service-principal-id> \
     --role "Monitoring Reader" \
     --scope "/subscriptions/<subscription-id>/resourceGroups/<resource-group>"
   ```

### Issue 5: Survey Variable Not Passed to Playbook

**Symptom:** Survey answer doesn't match expected variable in job output

**Solution:**
1. Verify **Variable name** in survey matches playbook variable:
   ```yaml
   # Survey variable name (from survey question)
   variable: azure_resource_group
   
   # Must match playbook extra_vars
   -e azure_resource_group=ml-platform-prod
   ```
2. Check job template **Extra vars** section:
   ```yaml
   operation: shutdown_compute
   azure_region: "eastus"
   ```
3. Verify survey variable is NOT duplicated in Extra vars (survey takes precedence)

### Issue 6: Multiple Choice Question Not Working

**Symptom:** Multiple choice options don't appear at launch

**Solution:**
1. In survey question, verify **Answer type** is set to **Multiple Choice**
2. Verify **Multiple choice options** field contains options (newline-separated):
   ```
   graceful (wait for jobs)
   immediate (no wait)
   ```
3. Each option should be on separate line (not comma-separated)
4. Click **Save** and re-launch to test

### Useful Debugging Commands

```bash
# View all job templates
awx-cli job_templates list

# View job execution logs
awx-cli jobs get <job-id> --format json | jq '.stdout'

# View scheduled jobs
awx-cli schedules list

# Test schedule syntax (cron)
# Install cronie-utils: yum install cronie-utils
cronolog -S <cron-expression>  # Verify expression

# Check AAP services
systemctl status awx-dispatcher
systemctl status awx-scheduler
systemctl status awx-web
systemctl status awx-rsyslog
```

---

## Summary

You now have 5 fully configured workflow templates for Azure ML cost optimization:

1. **Nightly Shutdown** (6pm weekdays) - Stop idle clusters
2. **Morning Startup** (8am weekdays) - Start clusters for business
3. **Weekly Right-Sizing** (2am Sunday) - Downsize underutilized resources
4. **Hourly PTU Management** (every hour) - Optimize OpenAI PTU
5. **Monthly ROI Report** (1st of month, 9am) - Generate cost savings report

Each template includes:
- Configured job template with playbook
- Survey questions for runtime customization
- Automated schedule for periodic execution
- Error handling and logging

### Next Steps

1. Deploy templates to production AAP environment
2. Run test executions for each template
3. Verify scheduled execution works correctly
4. Set up notifications for job completion
5. Train operations team on manual execution and troubleshooting
