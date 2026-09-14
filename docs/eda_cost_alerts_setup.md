# Event-Driven Ansible (EDA) Cost Alerts Setup Guide

This guide provides comprehensive instructions for setting up Event-Driven Ansible to monitor Azure Cost Management events and trigger automated cost optimization responses.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Azure Event Grid Setup](#azure-event-grid-setup)
5. [Service Bus Configuration](#service-bus-configuration)
6. [EDA Controller Setup](#eda-controller-setup)
7. [Rulebook Configuration](#rulebook-configuration)
8. [Testing & Validation](#testing--validation)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Event-Driven Ansible (EDA) monitors Azure Cost Management events and automatically triggers cost optimization actions when budget thresholds are exceeded or cost anomalies are detected.

### Benefits

- **Immediate Response:** Shut down resources within seconds of budget alert
- **No Schedule Needed:** React to actual cost spikes, not fixed schedules
- **Integrated with AAP:** Leverages existing AAP job templates and workflows
- **Auditability:** All triggered actions logged and traceable to cost events

### Key Use Cases

1. **Budget Threshold Alert** (80% of budget)
   - Trigger: Azure Cost Management event when budget reaches 80%
   - Action: Immediate shutdown of non-critical compute clusters
   - Expected Savings: $2,000-5,000 per event

2. **Cost Anomaly Detection**
   - Trigger: Unexpected cost spike detected (e.g., 20% over baseline)
   - Action: Generate immediate ROI report and alert team
   - Expected Result: Identify root cause and take corrective action

3. **Resource Quota Exceeded**
   - Trigger: Compute cluster count exceeds configured maximum
   - Action: Alert operations team and optionally trigger right-sizing

---

## Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Cloud Environment                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Azure Cost Management                                      │
│    └─> Generates budget alerts & cost anomaly events       │
│        (JSON events with cost, resource group, threshold)   │
│                                                              │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────┐
        │  Azure Event Grid               │
        │  System Topic: Cost Management  │
        │  Event Types: Budget.Exceeded   │
        │             Cost.Anomaly        │
        └─────────────┬───────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │  Azure Service Bus              │
        │  Queue: cost-management-events  │
        │  Messages: Event notifications  │
        └─────────────┬───────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │  Event-Driven Ansible           │
        │  (EDA Controller)               │
        │                                 │
        │  Rulebook:                      │
        │    Monitor Service Bus for:     │
        │      - Budget.Exceeded event    │
        │      - Cost.Anomaly event       │
        │                                 │
        │  When event detected:           │
        │    └─> Run AAP Job Template     │
        │        (shutdown_compute)       │
        │        (generate_roi_report)    │
        └──────────────┬──────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │  Ansible Automation Platform    │
        │  Job Templates:                 │
        │    • Cost Optimization Shutdown │
        │    • Cost Optimization Report   │
        │                                 │
        │  Actions:                       │
        │    • Emergency cluster shutdown │
        │    • Generate cost alert report │
        └─────────────┬───────────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │  Azure ML Infrastructure        │
        │  Compute Clusters → STOPPED     │
        │  OpenAI PTU → REDUCED           │
        └─────────────────────────────────┘
```

### Event Processing Flow

```
Event Detection → Rule Evaluation → Action Execution → Audit Logging
   (Event Grid)   (EDA Rulebook)  (AAP Job Template)  (Logs + Report)
```

---

## Prerequisites

### Azure Requirements

- **Azure Subscription** with:
  - Cost Management enabled
  - Budget configured for ML resource group
  - Event Grid system topic support
  - Service Bus Standard or Premium namespace

### AAP Requirements

- **Ansible Automation Platform 2.4+**
- **EDA (Event-Driven Ansible) plugin** installed:
  ```bash
  # On AAP controller
  ansible-galaxy collection install ansible.eda
  ```
- **Azure Event Grid plugin** for EDA:
  ```bash
  # On EDA controller
  ansible-galaxy collection install microsoft.azure_eventgrid
  ```

### Access Requirements

- **Azure Service Principal** with roles:
  - `Contributor` (for shutdown operations)
  - `Cost Management Reader` (for cost data access)
  - `Event Grid Resource Provider` (for Event Grid configuration)

- **AAP Credentials:**
  - Existing Azure Service Principal credential
  - New EDA service account (optional, for controller authentication)

### Network Requirements

- **Event Grid → Service Bus:** Already handled by Azure
- **EDA Controller → Service Bus:** Network connectivity required
  - Service Bus connection string accessible from EDA controller
  - Firewall rules allow Service Bus inbound (port 443)
  - If on-premises: VPN/ExpressRoute to Azure or hybrid cloud setup

---

## Azure Event Grid Setup

### Step 1: Create Azure Event Grid System Topic

The Event Grid system topic receives cost management events from Azure.

```bash
# Variables
RESOURCE_GROUP="ml-platform-prod"
TOPIC_NAME="cost-management-topic"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create system topic for cost management
az eventgrid system-topic create \
  --name $TOPIC_NAME \
  --resource-group $RESOURCE_GROUP \
  --source "/subscriptions/$SUBSCRIPTION_ID" \
  --topic-type Microsoft.CostManagement.Budgets

# Output: System topic created
# Note: This must be done in the Azure Portal or using Azure CLI with proper permissions
```

**Alternative (Azure Portal):**

1. Navigate to **Cost Management** → **Budgets**
2. Select your budget (or create new one)
3. In budget details, find **Events** or **Integrations** section
4. Enable event notifications
5. Configure destination: Event Grid system topic

### Step 2: Create Azure Budget (if not exists)

Cost Management events are triggered by budgets. Configure at least one budget:

```bash
# Create budget for ML resource group
az costmanagement budget create \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
  --name "ML-Platform-Monthly" \
  --category Unblocked \
  --amount 20000 \
  --time-grain Monthly \
  --start-date "2026-09-01" \
  --notifications '[
    {
      "enabled": true,
      "operator": "GreaterThanOrEqualTo",
      "threshold": 80,
      "contact_emails": ["team@example.com"]
    }
  ]'
```

**Budget Configuration Options:**

| Option | Value | Description |
|--------|-------|-------------|
| Category | Unblocked | Cost type (Unblocked = all resources) |
| Amount (USD) | 20000 | Monthly budget threshold |
| Time Grain | Monthly | Budget period |
| Threshold | 80 | Trigger event at 80% of budget |
| Contact Emails | team@example.com | Notification recipients |

**Event Types Generated:**
- Threshold reached (80% of budget)
- Hard limit exceeded (100% of budget)
- Forecast exceeded (projected overage)

### Step 3: List Event Grid Topics and Verify

```bash
# List all system topics in resource group
az eventgrid system-topic list \
  --resource-group $RESOURCE_GROUP \
  --output table

# Output:
# Name                      Location    ProvisioningState    Topic Type
# ─────────────────────────────────────────────────────────────────────
# cost-management-topic     eastus      Succeeded            Microsoft.CostManagement.Budgets
```

---

## Service Bus Configuration

### Step 1: Create Service Bus Namespace

Service Bus receives events from Event Grid and holds them in a queue for EDA to consume.

```bash
# Variables
SERVICE_BUS_NAMESPACE="ml-cost-events"
RESOURCE_GROUP="ml-platform-prod"

# Create Service Bus namespace (Standard tier for cost optimization)
az servicebus namespace create \
  --name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --sku Standard \
  --location eastus

# Verify creation
az servicebus namespace show \
  --name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP
```

### Step 2: Create Queue for Cost Events

The queue holds events that EDA will process.

```bash
# Create queue
az servicebus queue create \
  --name cost-management-events \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --max-size 1073741824 \
  --default-message-ttl P14D

# Verify queue
az servicebus queue show \
  --name cost-management-events \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP
```

**Queue Configuration:**
- **Name:** `cost-management-events`
- **Max Size:** 1GB (enough for high-volume events)
- **Message TTL:** 14 days (messages auto-delete after 14 days)
- **Duplicate Detection:** Enabled (prevents duplicate processing)

### Step 3: Get Service Bus Connection String

EDA needs the connection string to authenticate to Service Bus.

```bash
# Get connection string
CONNECTION_STRING=$(az servicebus namespace authorization-rule keys list \
  --name RootManageSharedAccessKey \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --query primaryConnectionString \
  -o tsv)

echo "Service Bus Connection String:"
echo $CONNECTION_STRING

# Output example:
# Endpoint=sb://ml-cost-events.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=ABCD1234...
```

**Store this connection string securely:**
- Do NOT check into version control
- Store in AAP Credentials or environment variable
- Use in EDA rulebook configuration (see next section)

### Step 4: Create Event Subscription (Event Grid → Service Bus)

This connects Event Grid to Service Bus, so events are delivered to the queue.

```bash
# Variables
TOPIC_NAME="cost-management-topic"
EVENT_SUBSCRIPTION="cost-to-servicebus"

# Get Event Grid topic resource ID
TOPIC_ID=$(az eventgrid system-topic show \
  --name $TOPIC_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Get Service Bus queue resource ID
QUEUE_ID=$(az servicebus queue show \
  --name cost-management-events \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Create event subscription
az eventgrid system-topic event-subscription create \
  --name $EVENT_SUBSCRIPTION \
  --system-topic-name $TOPIC_NAME \
  --resource-group $RESOURCE_GROUP \
  --endpoint-type servicebusqueue \
  --endpoint "$QUEUE_ID"

# Verify subscription
az eventgrid system-topic event-subscription show \
  --name $EVENT_SUBSCRIPTION \
  --system-topic-name $TOPIC_NAME \
  --resource-group $RESOURCE_GROUP
```

**Verification Checklist:**
- [ ] Event Grid system topic created
- [ ] Service Bus namespace created
- [ ] Service Bus queue created
- [ ] Event subscription connects Grid to queue
- [ ] Connection string obtained and secured

---

## EDA Controller Setup

### Step 1: Install EDA on Automation Platform

EDA is installed as part of AAP 2.4+ setup. Verify installation:

```bash
# On AAP controller
ansible-galaxy collection list | grep eda

# Output should show:
# ansible.eda  [version]
```

If not installed:

```bash
# Install EDA collection
ansible-galaxy collection install ansible.eda

# Install Azure EDA plugin (optional, for direct Azure integration)
ansible-galaxy collection install microsoft.azure_eventgrid
```

### Step 2: Configure EDA Runner

EDA processes run independently from AAP controller. Configure the EDA runner:

```bash
# Create EDA configuration directory
mkdir -p /etc/eda/ansible.cfg.d

# Create runner configuration
cat > /etc/eda/runner_config.yml << 'EOF'
---
private_data_dir: /var/lib/eda-runner
artifact_data_dir: /var/lib/eda-runner/artifacts
credentials_provider: env
EOF

# Create systemd service for EDA (if not already present)
# This ensures EDA runs continuously
systemctl enable eda-runner
systemctl start eda-runner
systemctl status eda-runner
```

### Step 3: Configure Azure Service Bus Connection

The EDA rulebook needs the Service Bus connection string. Store it securely:

**Option A: Environment Variable (Recommended for testing)**

```bash
# Export environment variable
export AZURE_SERVICE_BUS_CONNECTION=$(az servicebus namespace authorization-rule keys list \
  --name RootManageSharedAccessKey \
  --namespace-name ml-cost-events \
  --resource-group ml-platform-prod \
  --query primaryConnectionString -o tsv)

# Verify
echo $AZURE_SERVICE_BUS_CONNECTION
```

**Option B: Ansible Variable (Recommended for production)**

Create a variable file:

```bash
# File: /etc/eda/vars/service_bus_vars.yml
cat > /etc/eda/vars/service_bus_vars.yml << 'EOF'
---
azure_service_bus_connection: "Endpoint=sb://ml-cost-events.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR_KEY_HERE"
azure_service_bus_queue: "cost-management-events"
EOF

# Secure file permissions
chmod 600 /etc/eda/vars/service_bus_vars.yml
chown eda:eda /etc/eda/vars/service_bus_vars.yml
```

**Option C: AAP Credential (Production - Best Practice)**

1. In AAP UI: **Resources** → **Credentials** → **Create**
2. Select **Credential Type:** `Azure Service Bus`
3. Fill in:
   - **Name:** `Azure Service Bus - Cost Management`
   - **Connection String:** (paste Service Bus connection string)
4. Click **Save**

Then reference in rulebook:
```yaml
- ansible.eda.azure_service_bus:
    connection_str: "{{ lookup('ansible.builtin.env', 'AZURE_SERVICE_BUS_CONNECTION') }}"
```

---

## Rulebook Configuration

### Rulebook Overview

An EDA rulebook is a YAML file that defines:
- **Sources:** Where events come from (Service Bus)
- **Rules:** What conditions to watch for
- **Actions:** What to do when conditions are met

### Create Rulebook File

Create the cost alert rulebook:

```bash
# Create rulebook file
mkdir -p /etc/eda/rulesets
cat > /etc/eda/rulesets/cost_alerts.yml << 'EOF'
---
- name: Azure Cost Management event-driven automation
  hosts: all
  
  sources:
    - ansible.eda.azure_service_bus:
        connection_str: "{{ azure_service_bus_connection }}"
        queue_name: "cost-management-events"
        max_queue_depth: 10
  
  rules:
    - name: Budget threshold exceeded (80%) - emergency shutdown
      condition: event.data.costThreshold >= 80
      action:
        run_job_template:
          name: "Cost Optimization - Shutdown Compute"
          organization: "Default"
          extra_vars:
            operation: "shutdown_compute"
            emergency_mode: true
            budget_alert_action: "shutdown_non_critical"
            azure_resource_group: "{{ event.data.resourceGroup | default('ml-platform-prod') }}"
            shutdown_mode: "immediate"
            preserve_running_jobs: false
      throttle:
        once: true
        group_by: ["event.data.resourceGroup"]
    
    - name: Cost anomaly detected - generate ROI report
      condition: event.data.costAnomaly == true or (event.data.costDelta | default(0)) > 20
      action:
        run_job_template:
          name: "Cost Optimization - ROI Report"
          organization: "Default"
          extra_vars:
            operation: "generate_roi_report"
            alert_team: true
            azure_resource_group: "{{ event.data.resourceGroup | default('ml-platform-prod') }}"
            anomaly_detected: true
      throttle:
        once: true
        group_by: ["event.data.resourceGroup"]
    
    - name: Multiple budget alerts - escalate to team
      condition: event.data.costThreshold >= 90
      action:
        debug:
          msg: |
            CRITICAL: Cost threshold at {{ event.data.costThreshold }}% for {{ event.data.resourceGroup }}
            Trigger immediate escalation to team
            Alert recipients: team@example.com
      throttle:
        once: true
        group_by: ["event.data.resourceGroup"]
EOF

# Verify rulebook syntax
ansible-lint /etc/eda/rulesets/cost_alerts.yml
```

### Rulebook Explanation

**Sources Section:**
```yaml
sources:
  - ansible.eda.azure_service_bus:
      connection_str: "{{ azure_service_bus_connection }}"  # Connection string variable
      queue_name: "cost-management-events"                  # Queue to monitor
      max_queue_depth: 10                                   # Process up to 10 messages per interval
```

**Rules Section - Rule 1 (Budget Threshold):**
```yaml
- name: Budget threshold exceeded (80%) - emergency shutdown
  condition: event.data.costThreshold >= 80  # Trigger if budget >= 80%
  action:
    run_job_template:
      name: "Cost Optimization - Shutdown Compute"
      extra_vars:
        operation: "shutdown_compute"
        emergency_mode: true                    # Skip graceful wait
        budget_alert_action: "shutdown_non_critical"  # Only stop non-critical clusters
        shutdown_mode: "immediate"              # Immediate, don't wait for jobs
```

**Rules Section - Rule 2 (Cost Anomaly):**
```yaml
- name: Cost anomaly detected - generate ROI report
  condition: event.data.costDelta > 20  # Trigger if cost spike > 20%
  action:
    run_job_template:
      name: "Cost Optimization - ROI Report"
      extra_vars:
        operation: "generate_roi_report"
        anomaly_detected: true            # Flag for special report format
```

**Rules Section - Rule 3 (Escalation):**
```yaml
- name: Multiple budget alerts - escalate to team
  condition: event.data.costThreshold >= 90  # Critical threshold (90%)
  action:
    debug:
      msg: "Alert team about critical cost situation"
```

### Advanced Rulebook Configuration

#### Custom Event Processing

```yaml
- name: Process complex cost events with transformation
  condition: |
    event.data.costThreshold >= 80 and 
    event.data.resourceGroup == "ml-platform-prod" and
    event.data.eventType == "BudgetExceeded"
  action:
    set_fact:
      cost_event:
        timestamp: "{{ now(utc=True) }}"
        threshold: "{{ event.data.costThreshold }}"
        resource_group: "{{ event.data.resourceGroup }}"
        action: "emergency_shutdown"
```

#### Multiple Actions from Single Event

```yaml
- name: Budget exceeded - multi-step response
  condition: event.data.costThreshold >= 80
  action:
    run_job_template:
      name: "Cost Optimization - Shutdown Compute"
      extra_vars:
        operation: "shutdown_compute"
  then:
    - name: Generate report
      action:
        run_job_template:
          name: "Cost Optimization - ROI Report"
    
    - name: Send notification
      action:
        debug:
          msg: "Cost optimization actions completed"
```

---

## Testing & Validation

### Test 1: Verify Service Bus Connectivity

Check that events can be received from Service Bus:

```bash
# Install Service Bus explorer tool
pip install azure-servicebus

# Test connection
python3 << 'EOF'
from azure.servicebus import ServiceBusClient
from azure.identity import DefaultAzureCredential

connection_str = "Endpoint=sb://ml-cost-events.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=..."

with ServiceBusClient.from_connection_string(connection_str) as client:
    with client.get_queue_receiver("cost-management-events") as receiver:
        messages = receiver.receive_messages(max_message_count=1, max_wait_time=5)
        if messages:
            print(f"Received {len(messages)} messages from queue")
            for msg in messages:
                print(f"Message: {msg.body}")
        else:
            print("Queue is empty (no messages received)")
EOF
```

### Test 2: Send Test Event to Service Bus

Manually send a test event to verify rulebook processing:

```bash
# Create test event payload
python3 << 'EOF'
import json
from azure.servicebus import ServiceBusClient

connection_str = "Endpoint=sb://ml-cost-events.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=..."
queue_name = "cost-management-events"

test_event = {
    "eventType": "BudgetExceeded",
    "eventTime": "2026-09-10T14:30:00Z",
    "data": {
        "resourceGroup": "ml-platform-prod",
        "costThreshold": 85,
        "currentCost": 17000,
        "budgetLimit": 20000,
        "costDelta": 25,
        "costAnomaly": True
    }
}

with ServiceBusClient.from_connection_string(connection_str) as client:
    with client.get_queue_sender(queue_name) as sender:
        message_body = json.dumps(test_event)
        sender.send_message(message_body)
        print(f"Test event sent: {test_event}")
EOF
```

### Test 3: Monitor EDA Rulebook Execution

Watch EDA logs to see rulebook processing:

```bash
# Check EDA runner logs (if systemd service)
journalctl -u eda-runner -f

# Or check EDA container logs (if containerized)
docker logs eda-runner

# Or check log file directly
tail -f /var/log/eda/eda-runner.log
```

**Expected Output:**
```
2026-09-10 14:30:15 - EDA Rulebook loaded: cost_alerts.yml
2026-09-10 14:30:20 - Azure Service Bus source connected
2026-09-10 14:30:25 - Event received: BudgetExceeded (costThreshold: 85%)
2026-09-10 14:30:25 - Rule matched: "Budget threshold exceeded"
2026-09-10 14:30:26 - Action triggered: run_job_template "Cost Optimization - Shutdown Compute"
2026-09-10 14:30:27 - Job template launched with ID: 12345
```

### Test 4: Trigger Real Budget Alert

Generate actual cost by running temporary workloads:

1. **Create temporary test cluster:**
   ```bash
   # Create a small test cluster to generate costs
   az ml compute create \
     --name test-cost-tracker \
     --type AmlCompute \
     --vm-size Standard_DS3_v2 \
     --min-instances 4 \
     --max-instances 4 \
     --idle-seconds-before-scaledown 0
   ```

2. **Monitor costs:**
   ```bash
   # Check costs in real-time
   az costmanagement query create \
     --scope "/subscriptions/$SUBSCRIPTION_ID" \
     --timeframe MonthToDate \
     --dataset-aggregation totalCost="{name: 'Cost', function: 'Sum'}" \
     --type ActualCost
   ```

3. **Wait for budget threshold:**
   - Monitor Cost Management dashboard
   - When threshold is reached, budget alert fires
   - Event Grid sends message to Service Bus
   - EDA processes event and triggers shutdown

4. **Verify shutdown occurred:**
   ```bash
   # Check cluster state
   az ml compute show --name test-cost-tracker
   
   # Should show: provisioning_state = "Stopped"
   ```

### Test 5: Verify Throttling Logic

Test that rules don't fire excessively:

```yaml
# Add throttle configuration to rules
throttle:
  once: true                           # Fire rule only once
  group_by: ["event.data.resourceGroup"]  # Per resource group
  
  # Alternative: time-based throttling
  throttle:
    every: 300  # Fire rule only every 5 minutes (300 seconds)
```

**Verify throttling:**
1. Send 10 identical test events
2. Check logs - rule should fire only once
3. Wait 5 minutes
4. Send another event - rule should fire again

---

## Troubleshooting

### Issue 1: "Connection to Service Bus Failed"

**Symptom:** EDA logs show connection error
```
ERROR: Failed to connect to Service Bus
```

**Diagnosis:**
```bash
# Test connection manually
python3 -c "
from azure.servicebus import ServiceBusClient
client = ServiceBusClient.from_connection_string('YOUR_CONNECTION_STRING')
print('Connected successfully')
"
```

**Solution:**
1. Verify connection string is correct (copy from Azure Portal)
2. Check network connectivity from EDA controller to Azure
   ```bash
   curl -v amqps://ml-cost-events.servicebus.windows.net:5671/
   ```
3. Verify Service Bus namespace is accessible:
   ```bash
   az servicebus namespace show --name ml-cost-events --resource-group ml-platform-prod
   ```

### Issue 2: "No Events Received from Service Bus"

**Symptom:** EDA rulebook running but no events detected
```
EDA Rulebook loaded but no events received
```

**Diagnosis:**
1. Verify Event Grid is connected to Service Bus:
   ```bash
   az eventgrid system-topic event-subscription show \
     --name cost-to-servicebus \
     --system-topic-name cost-management-topic \
     --resource-group ml-platform-prod
   ```

2. Check if budget events are being generated:
   ```bash
   # View events in Event Grid
   az eventgrid system-topic-event-subscription event list \
     --system-topic-name cost-management-topic \
     --resource-group ml-platform-prod
   ```

3. Verify Service Bus queue is receiving messages:
   ```bash
   az servicebus queue show \
     --name cost-management-events \
     --namespace-name ml-cost-events \
     --resource-group ml-platform-prod
   # Check "messageCount" in output
   ```

**Solution:**
- Verify budget is configured and active
- Check budget threshold is realistic (e.g., not $1 million)
- Manually send test event (see Test 2 above)
- Check Event Grid subscription is enabled

### Issue 3: "Job Template Launch Failed"

**Symptom:** Rule matches but job template doesn't launch
```
ERROR: Failed to launch job template "Cost Optimization - Shutdown Compute"
```

**Diagnosis:**
1. Verify job template exists:
   ```bash
   awx-cli job_templates list | grep "Cost Optimization"
   ```

2. Check job template is in correct organization:
   ```bash
   awx-cli job_templates get --filter 'name="Cost Optimization - Shutdown Compute"'
   ```

3. Check credentials are available:
   ```bash
   awx-cli credentials list | grep "Azure"
   ```

**Solution:**
- Verify job template name matches exactly
- Check job template organization matches rulebook (`--organization "Default"`)
- Verify Azure credentials are configured in AAP
- Check AAP service is running: `systemctl status awx-service`

### Issue 4: "Extra Variables Not Passed to Job"

**Symptom:** Job launches but uses default values instead of event data
```
Job ran with default azure_resource_group instead of event value
```

**Diagnosis:**
1. Check rulebook extra_vars syntax:
   ```yaml
   extra_vars:
     operation: "shutdown_compute"
     azure_resource_group: "{{ event.data.resourceGroup }}"  # Should use Jinja2 syntax
   ```

2. Verify event.data has expected fields:
   ```bash
   # Enable debug logging
   EDA_LOG_LEVEL=DEBUG eda-runner -r /etc/eda/rulesets/cost_alerts.yml
   ```

**Solution:**
- Ensure Jinja2 template syntax: `{{ event.data.fieldName }}`
- Verify event JSON has expected fields
- Add default values for missing fields: `{{ event.data.resourceGroup | default('ml-platform-prod') }}`

### Issue 5: "Rulebook Syntax Error"

**Symptom:** EDA fails to load rulebook
```
ERROR: Failed to parse rulebook: YAML syntax error
```

**Solution:**
1. Validate YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('/etc/eda/rulesets/cost_alerts.yml'))"
   ```

2. Validate Jinja2 templates:
   ```bash
   ansible-lint /etc/eda/rulesets/cost_alerts.yml
   ```

3. Check indentation (YAML is whitespace-sensitive)
   - Use spaces, not tabs
   - Consistent indentation (2 spaces per level)

### Issue 6: "Service Bus Queue Has Backlog"

**Symptom:** Queue has thousands of pending messages
```
Queue depth: 10,000 messages (HIGH)
```

**Cause:** Events accumulating faster than being processed

**Solution:**
1. Increase rulebook processing frequency:
   ```yaml
   sources:
     - ansible.eda.azure_service_bus:
         max_queue_depth: 50  # Process more messages per interval
   ```

2. Add rule throttling to prevent duplicate actions:
   ```yaml
   throttle:
     every: 60  # Process same rule only every 60 seconds
   ```

3. Monitor Event Grid event volume:
   ```bash
   # Check events in Event Grid
   az eventgrid system-topic-event-subscription event list \
     --system-topic-name cost-management-topic
   ```

4. If events are genuinely high, consider:
   - Adjusting budget thresholds (less frequent events)
   - Creating separate queues for different event types
   - Scaling up Service Bus (Premium tier for higher throughput)

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set EDA log level to DEBUG
export EDA_LOG_LEVEL=DEBUG

# Run rulebook with verbose output
eda-runner -r /etc/eda/rulesets/cost_alerts.yml -v

# Enable Ansible debug logging
export ANSIBLE_DEBUG=true

# Check system logs
journalctl -u eda-runner -n 100 --follow
```

---

## Production Checklist

Before deploying to production, verify:

### Infrastructure
- [ ] Azure Event Grid system topic created
- [ ] Service Bus namespace created with Standard or Premium tier
- [ ] Service Bus queue created with appropriate TTL
- [ ] Event subscription connects Grid to queue
- [ ] Network connectivity from EDA to Service Bus verified

### AAP Configuration
- [ ] Azure Service Principal credential configured
- [ ] Cost Optimization job templates exist and are functional
- [ ] Job templates have correct playbook paths
- [ ] AAP scheduler service is running

### EDA Configuration
- [ ] EDA runner installed and enabled
- [ ] Rulebook syntax validated
- [ ] Service Bus connection string securely stored
- [ ] Rulebook tested with manual event injection

### Monitoring & Alerting
- [ ] EDA logs configured to send to monitoring system
- [ ] Job template executions logged and auditable
- [ ] Team notification channels configured (email, Slack)
- [ ] Budget thresholds configured and realistic

### Safety & Compliance
- [ ] "preserve_running_jobs: true" set for non-emergency shutdowns
- [ ] Resource tagging strategy for critical resources
- [ ] Audit logging enabled for all actions
- [ ] Rollback procedures documented

---

## References

- [Azure Event Grid Documentation](https://docs.microsoft.com/en-us/azure/event-grid/)
- [Azure Service Bus Documentation](https://docs.microsoft.com/en-us/azure/service-bus-messaging/)
- [Event-Driven Ansible Documentation](https://ansible.readthedocs.io/en/latest/collections/ansible/eda/azure_service_bus_source.html)
- [Azure Cost Management Events](https://docs.microsoft.com/en-us/azure/cost-management-billing/costs/)
- [AAP Job Template Documentation](https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/)
