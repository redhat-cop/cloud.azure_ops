# Multi-Environment Azure ML Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable `multi_env_ml_deployment` role (invoked from an example playbook) that provisions dev/staging/prod Azure ML environments and governs model promotion across them with automated + approval gates, an immutable audit trail, and per-environment network isolation.

**Architecture:** A single Ansible role with an operation router (`include_tasks: "{{ operation }}.yml"`, matching `self_service_ml_platform`). Operations provision shared hub resources (RG, ML Registry, Key Vault, ACR, App Insights, audit storage), provision one environment's spoke resources (storage + workspace + compute), and promote a model between environments through gates while recording audit events. Per-environment differences are driven by one `azure_ml_menv_environments` dict. The example playbook orchestrates the full cycle.

**Tech Stack:** Ansible (ansible-core 2.19), `azure.azcollection` (`azure_rm_*` and `azure_rm_ml_*` modules), `cloud.azure_ops` roles (`azure_manage_resource_group`, `azure_manage_storage_account`), Azure Machine Learning, `ansible-test integration` against live Azure.

**Spec:** `docs/superpowers/specs/2026-09-18-multi-env-ml-deployment-design.md`

## Global Constraints

- **ansible-core:** 2.19. `until:`/`retries:` does NOT retry a *crashed* module (only clean `fail_json`/non-zero rc). Do not rely on `until:` to survive module crashes.
- **Resource tags (mandatory):** every Azure resource created MUST carry tags `environment`, `cost_center`, and `team`. Source them from `azure_ml_menv_tags` (a computed dict) so they are parameterizable.
- **Azure name length limits:** storage account ≤ 24 (alphanumeric lowercase), Key Vault ≤ 24, ML workspace ≤ 33, ML registry ≤ 33, online endpoint ≤ 32. Always truncate names derived from `azure_resource_group`.
- **Router contract:** `operation` values MUST equal a task-file basename in `roles/multi_env_ml_deployment/tasks/`.
- **Idempotency:** provision tasks must be safe to re-run. Delete tasks use `failed_when: false` and always reach resource-group deletion.
- **Naming:** role + playbook + doc named `multi_env_ml_deployment`; role variables prefixed `azure_ml_menv_`; router var is bare `operation`; region var is bare `azure_region` (matches `self_service_ml_platform` / `mlops_lifecycle`).
- **galaxy.yml:** bump `version` `6.1.2` → `6.2.0`.
- **Local validation:** `yamllint <file>` on every new YAML file; `ansible-playbook --syntax-check` on the example playbook. `ansible-lint` is currently broken locally (Python 3.14) — do not gate on it. Live Azure tests run only via CI `ansible-test integration`.
- **Integration tests:** live Azure. Test target must be self-contained: create a dedicated RG `{{ resource_prefix }}-mlmenv`, use it, delete it in `always:`. Never delete the shared `resource_group`. Pass distinct test var names into `include_role` (e.g. `test_azure_region`) to avoid recursive-template errors.

---

## Reference variable model (used across all tasks)

These names are the shared contract between tasks. `defaults/main.yml` (Task 1) defines them; every later task consumes them.

```yaml
operation: provision_shared_infrastructure   # router selector
azure_region: eastus
azure_ml_menv_environment: dev               # active env for env-scoped operations

# Per-environment configuration (the governance story)
azure_ml_menv_environments:
  dev:     { code: dev,  public_network_access: Enabled,  compute_max_nodes: 4, requires_approval: false }
  staging: { code: stg,  public_network_access: Disabled, compute_max_nodes: 2, requires_approval: true }
  prod:    { code: prod, public_network_access: Disabled, compute_max_nodes: 2, requires_approval: true }

# Tags (global constraint)
azure_ml_menv_environment_tag: production
azure_ml_menv_cost_center: ml-platform
azure_ml_menv_team: ml-platform
azure_ml_menv_tags:
  environment: "{{ azure_ml_menv_environment_tag }}"
  cost_center: "{{ azure_ml_menv_cost_center }}"
  team: "{{ azure_ml_menv_team }}"

# Shared (hub) resource names
azure_ml_menv_keyvault_name: "{{ azure_resource_group[:19] }}-mkv"
azure_ml_menv_acr_name: "{{ (azure_resource_group | regex_replace('[^a-z0-9]', ''))[:43] }}menvacr"
azure_ml_menv_appinsights_name: "{{ azure_resource_group }}-menv-ai"
azure_ml_menv_registry_name: "{{ azure_resource_group[:20] }}-menvreg"
azure_ml_menv_audit_storage_account: "{{ (azure_resource_group | regex_replace('[^a-z0-9]', ''))[:15] }}auditml"
azure_ml_menv_audit_container: audit

# Per-environment (spoke) resource names — computed from the active env code
azure_ml_menv_env_code: "{{ azure_ml_menv_environments[azure_ml_menv_environment].code }}"
azure_ml_menv_storage_account: "{{ (azure_resource_group | regex_replace('[^a-z0-9]', ''))[:16] }}{{ azure_ml_menv_env_code }}ml"
azure_ml_menv_workspace_name: "{{ azure_resource_group[:22] }}-ml-{{ azure_ml_menv_env_code }}"
azure_ml_menv_compute_name: training-cluster
azure_ml_menv_compute_vm_size: Standard_DS3_v2
azure_ml_menv_storage_container: training-data

# Model + promotion
azure_ml_menv_model_name: menv-model
azure_ml_menv_model_version: "1"
azure_ml_menv_min_accuracy: 0.90            # automated gate threshold
azure_ml_menv_promotion_approved: false     # manual approval gate (AAP node supplies true)
azure_ml_menv_use_registry: true            # publish to shared ML registry (best-effort)

# Audit context
azure_ml_menv_actor: "{{ lookup('ansible.builtin.env', 'AZURE_CLIENT_ID') | default('unknown', true) }}"
azure_ml_menv_correlation_id: "{{ now(true, '%Y%m%dT%H%M%SZ') }}"

# Service principal (registry role assignment)
azure_client_id: "{{ lookup('ansible.builtin.env', 'AZURE_CLIENT_ID') }}"
azure_secret: "{{ lookup('ansible.builtin.env', 'AZURE_SECRET') }}"
azure_tenant: "{{ lookup('ansible.builtin.env', 'AZURE_TENANT') }}"
```

---

## Task 1: Role scaffolding (defaults, router, README skeleton)

**Files:**
- Create: `roles/multi_env_ml_deployment/defaults/main.yml`
- Create: `roles/multi_env_ml_deployment/tasks/main.yml`
- Create: `roles/multi_env_ml_deployment/README.md`
- Create: `roles/multi_env_ml_deployment/meta/argument_specs.yml` (optional but matches collection convention if present elsewhere — skip if no other role has one)

**Interfaces:**
- Produces: the full variable contract in "Reference variable model" above; the router `include_tasks: "{{ operation }}.yml"`.

- [ ] **Step 1: Write `defaults/main.yml`** with the entire "Reference variable model" block above (verbatim).

- [ ] **Step 2: Write `tasks/main.yml` router**

```yaml
---
- name: Fail when azure_resource_group is not defined
  ansible.builtin.fail:
    msg: azure_resource_group must be defined
  when: azure_resource_group is not defined

- name: Include operation-specific tasks
  ansible.builtin.include_tasks: "{{ operation }}.yml"
  when: operation is defined
```

- [ ] **Step 3: Write `README.md`** documenting the role: purpose, operations table (`provision_shared_infrastructure`, `provision_environment`, `promote_model`, `delete_environment`, `delete_shared_infrastructure`), the `azure_ml_menv_environments` dict, gate variables, audit behavior, and an example invocation per operation. (Model structure on `roles/self_service_ml_platform/README.md`.)

- [ ] **Step 4: Validate**

Run: `yamllint roles/multi_env_ml_deployment/defaults/main.yml roles/multi_env_ml_deployment/tasks/main.yml`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add roles/multi_env_ml_deployment/defaults roles/multi_env_ml_deployment/tasks/main.yml roles/multi_env_ml_deployment/README.md
git commit -m "feat: scaffold multi_env_ml_deployment role (ACA-5889)"
```

---

## Task 2: Audit event helper (`record_audit_event.yml`)

**Files:**
- Create: `roles/multi_env_ml_deployment/tasks/record_audit_event.yml`

**Interfaces:**
- Consumes (task vars set by caller before `include_tasks`): `audit_action` (str, required), `audit_environment` (str, default `""`), `audit_model_name` (str, default `""`), `audit_model_version` (str, default `""`), `audit_approval_status` (str, default `not_required`), `audit_gate_result` (str, default `skipped`).
- Consumes (role vars): `azure_ml_menv_audit_storage_account`, `azure_ml_menv_audit_container`, `azure_resource_group`, `azure_ml_menv_actor`, `azure_ml_menv_correlation_id`, `azure_ml_menv_tags`.
- Produces: one immutable blob `audit/<timestamp>-<action>.json` in the audit container.

- [ ] **Step 1: Write `record_audit_event.yml`**

```yaml
---
- name: Build audit record for action {{ audit_action }}
  ansible.builtin.set_fact:
    _audit_timestamp: "{{ now(true, '%Y%m%dT%H%M%SZ') }}"
    _audit_record:
      timestamp: "{{ now(true, '%Y-%m-%dT%H:%M:%SZ') }}"
      action: "{{ audit_action }}"
      environment: "{{ audit_environment | default('') }}"
      model_name: "{{ audit_model_name | default('') }}"
      model_version: "{{ audit_model_version | default('') }}"
      actor: "{{ azure_ml_menv_actor }}"
      approval_status: "{{ audit_approval_status | default('not_required') }}"
      gate_result: "{{ audit_gate_result | default('skipped') }}"
      correlation_id: "{{ azure_ml_menv_correlation_id }}"

- name: Create temporary directory for audit record
  ansible.builtin.tempfile:
    state: directory
    prefix: menv_audit_
  register: _audit_tmpdir

- name: Write audit record to a local JSON file
  ansible.builtin.copy:
    dest: "{{ _audit_tmpdir.path }}/record.json"
    content: "{{ _audit_record | to_nice_json }}"
    mode: "0644"

- name: Upload audit record to the audit container
  azure.azcollection.azure_rm_storageblob:
    resource_group: "{{ azure_resource_group }}"
    storage_account_name: "{{ azure_ml_menv_audit_storage_account }}"
    container: "{{ azure_ml_menv_audit_container }}"
    blob: "audit/{{ _audit_timestamp }}-{{ audit_action }}.json"
    src: "{{ _audit_tmpdir.path }}/record.json"
    content_type: application/json

- name: Remove temporary audit directory
  ansible.builtin.file:
    path: "{{ _audit_tmpdir.path | default('/nonexistent') }}"
    state: absent
  when: _audit_tmpdir.path is defined
```

- [ ] **Step 2: Validate**

Run: `yamllint roles/multi_env_ml_deployment/tasks/record_audit_event.yml`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add roles/multi_env_ml_deployment/tasks/record_audit_event.yml
git commit -m "feat: add immutable audit-event recorder to multi_env_ml_deployment"
```

---

## Task 3: Shared infrastructure (`provision_shared_infrastructure.yml`)

**Files:**
- Create: `roles/multi_env_ml_deployment/tasks/provision_shared_infrastructure.yml`

**Interfaces:**
- Consumes: shared-name + tag vars from Task 1.
- Produces: RG, Key Vault, ACR, App Insights, ML Registry, audit storage account + `audit` container; sets facts `_menv_subscription_id`, `_menv_tenant_id`, `_menv_arm_prefix` (reused by later operations that run in the same play). Writes a `provision_shared` audit record.

- [ ] **Step 1: Write `provision_shared_infrastructure.yml`** (patterns proven in `playbooks/mlops_lifecycle.yml:19-123`; add tags everywhere and the audit storage):

```yaml
---
- name: Create resource group
  ansible.builtin.include_role:
    name: cloud.azure_ops.azure_manage_resource_group
  vars:
    azure_manage_resource_group_operation: create
    azure_manage_resource_group_name: "{{ azure_resource_group }}"
    azure_manage_resource_group_region: "{{ azure_region }}"

- name: Retrieve subscription and tenant info
  azure.azcollection.azure_rm_subscription_info:
  register: _sub_info

- name: Set subscription and tenant facts
  ansible.builtin.set_fact:
    _menv_subscription_id: "{{ _sub_info.subscriptions[0].subscription_id }}"
    _menv_tenant_id: "{{ _sub_info.subscriptions[0].tenant_id }}"
    _menv_arm_prefix: "/subscriptions/{{ _sub_info.subscriptions[0].subscription_id }}/resourceGroups/{{ azure_resource_group }}/providers"

- name: Create shared Key Vault
  azure.azcollection.azure_rm_keyvault:
    resource_group: "{{ azure_resource_group }}"
    vault_name: "{{ azure_ml_menv_keyvault_name }}"
    vault_tenant: "{{ _menv_tenant_id }}"
    location: "{{ azure_region }}"
    enable_rbac_authorization: true
    tags: "{{ azure_ml_menv_tags }}"
    sku:
      name: standard
      family: A

- name: Create shared Application Insights
  azure.azcollection.azure_rm_resource:
    resource_group: "{{ azure_resource_group }}"
    provider: Insights
    resource_type: components
    resource_name: "{{ azure_ml_menv_appinsights_name }}"
    api_version: "2020-02-02"
    idempotency: true
    body:
      location: "{{ azure_region }}"
      kind: web
      tags: "{{ azure_ml_menv_tags }}"
      properties:
        Application_Type: web

- name: Create shared Container Registry
  azure.azcollection.azure_rm_containerregistry:
    resource_group: "{{ azure_resource_group }}"
    name: "{{ azure_ml_menv_acr_name }}"
    location: "{{ azure_region }}"
    sku: Basic
    admin_user_enabled: false
    tags: "{{ azure_ml_menv_tags }}"

- name: Create audit storage account
  ansible.builtin.include_role:
    name: cloud.azure_ops.azure_manage_storage_account
  vars:
    azure_manage_storage_account_operation: create
    azure_manage_storage_account_name: "{{ azure_ml_menv_audit_storage_account }}"
    azure_manage_storage_account_resource_group: "{{ azure_resource_group }}"
    azure_manage_storage_account_region: "{{ azure_region }}"
    azure_manage_storage_account_container_name: "{{ azure_ml_menv_audit_container }}"

- name: Create shared ML registry for cross-environment model sharing
  azure.azcollection.azure_rm_ml_registry:
    resource_group: "{{ azure_resource_group }}"
    name: "{{ azure_ml_menv_registry_name }}"
    resource_definition: |
      location: {{ azure_region }}
      replication_locations:
        - location: {{ azure_region }}
  when: azure_ml_menv_use_registry | bool

- name: Record shared-infrastructure provisioning in the audit trail
  ansible.builtin.include_tasks: record_audit_event.yml
  vars:
    audit_action: provision_shared
    audit_gate_result: skipped
```

> Note: `azure_manage_storage_account` creates the audit container, so the `audit` container exists before `record_audit_event.yml` runs.

- [ ] **Step 2: Validate**

Run: `yamllint roles/multi_env_ml_deployment/tasks/provision_shared_infrastructure.yml`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add roles/multi_env_ml_deployment/tasks/provision_shared_infrastructure.yml
git commit -m "feat: add shared infrastructure provisioning to multi_env_ml_deployment"
```

---

## Task 4: Environment provisioning (`provision_environment.yml`)

**Files:**
- Create: `roles/multi_env_ml_deployment/tasks/provision_environment.yml`

**Interfaces:**
- Consumes: `azure_ml_menv_environment` (which env), the env config dict, shared-name vars. Re-derives ARM prefix locally (so the operation works even when invoked in a fresh play).
- Produces: per-env storage account, ML workspace (network access from env config), compute cluster; writes a `provision_environment` audit record.

- [ ] **Step 1: Write `provision_environment.yml`**

```yaml
---
- name: Resolve active environment configuration
  ansible.builtin.set_fact:
    _env_cfg: "{{ azure_ml_menv_environments[azure_ml_menv_environment] }}"

- name: Retrieve subscription info for ARM prefix
  azure.azcollection.azure_rm_subscription_info:
  register: _sub_info

- name: Set ARM prefix fact
  ansible.builtin.set_fact:
    _menv_arm_prefix: "/subscriptions/{{ _sub_info.subscriptions[0].subscription_id }}/resourceGroups/{{ azure_resource_group }}/providers"

- name: Create environment storage account
  ansible.builtin.include_role:
    name: cloud.azure_ops.azure_manage_storage_account
  vars:
    azure_manage_storage_account_operation: create
    azure_manage_storage_account_name: "{{ azure_ml_menv_storage_account }}"
    azure_manage_storage_account_resource_group: "{{ azure_resource_group }}"
    azure_manage_storage_account_region: "{{ azure_region }}"
    azure_manage_storage_account_container_name: "{{ azure_ml_menv_storage_container }}"

- name: Create ML workspace for environment {{ azure_ml_menv_environment }}
  azure.azcollection.azure_rm_ml_workspace:
    resource_group: "{{ azure_resource_group }}"
    name: "{{ azure_ml_menv_workspace_name }}"
    location: "{{ azure_region }}"
    display_name: "{{ azure_ml_menv_workspace_name }}"
    storage_account: "{{ _menv_arm_prefix }}/Microsoft.Storage/storageAccounts/{{ azure_ml_menv_storage_account }}"
    key_vault: "{{ _menv_arm_prefix }}/Microsoft.KeyVault/vaults/{{ azure_ml_menv_keyvault_name }}"
    application_insights: "{{ _menv_arm_prefix }}/Microsoft.Insights/components/{{ azure_ml_menv_appinsights_name }}"
    container_registry: "{{ _menv_arm_prefix }}/Microsoft.ContainerRegistry/registries/{{ azure_ml_menv_acr_name }}"
    public_network_access: "{{ _env_cfg.public_network_access }}"
    tags: "{{ azure_ml_menv_tags }}"

- name: Create compute cluster in environment {{ azure_ml_menv_environment }}
  azure.azcollection.azure_rm_ml_compute:
    resource_group: "{{ azure_resource_group }}"
    ml_workspace: "{{ azure_ml_menv_workspace_name }}"
    name: "{{ azure_ml_menv_compute_name }}"
    location: "{{ azure_region }}"
    type: amlcompute
    size: "{{ azure_ml_menv_compute_vm_size }}"
    min_instances: 0
    max_instances: "{{ _env_cfg.compute_max_nodes }}"
    idle_time_before_scale_down: 120

- name: Record environment provisioning in the audit trail
  ansible.builtin.include_tasks: record_audit_event.yml
  vars:
    audit_action: provision_environment
    audit_environment: "{{ azure_ml_menv_environment }}"
    audit_gate_result: skipped
```

- [ ] **Step 2: Validate**

Run: `yamllint roles/multi_env_ml_deployment/tasks/provision_environment.yml`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add roles/multi_env_ml_deployment/tasks/provision_environment.yml
git commit -m "feat: add per-environment provisioning to multi_env_ml_deployment"
```

---

## Task 5: Automated validation gate (`validate_promotion_gate.yml`)

**Files:**
- Create: `roles/multi_env_ml_deployment/tasks/validate_promotion_gate.yml`

**Interfaces:**
- Consumes (task vars): `gate_source_env` (str), `gate_target_env` (str). Consumes role vars `azure_ml_menv_model_name`, `azure_ml_menv_model_version`, `azure_ml_menv_min_accuracy`, `azure_ml_menv_environments`.
- Produces: fact `_menv_gate_result` (`passed`), fact `_menv_approval_status` (`approved`/`not_required`). Fails the play if the automated or approval gate is not satisfied.

- [ ] **Step 1: Write `validate_promotion_gate.yml`**

```yaml
---
- name: Resolve source workspace name for gate lookup
  ansible.builtin.set_fact:
    _gate_source_workspace: "{{ azure_resource_group[:22] }}-ml-{{ azure_ml_menv_environments[gate_source_env].code }}"
    _gate_target_cfg: "{{ azure_ml_menv_environments[gate_target_env] }}"

- name: Look up candidate model in source workspace
  azure.azcollection.azure_rm_ml_model_info:
    resource_group: "{{ azure_resource_group }}"
    ml_workspace: "{{ _gate_source_workspace }}"
    name: "{{ azure_ml_menv_model_name }}"
    version: "{{ azure_ml_menv_model_version }}"
  register: _gate_model

- name: Extract candidate model accuracy from tags
  ansible.builtin.set_fact:
    _gate_accuracy: "{{ (_gate_model.ml_models[0].tags.accuracy | default(0)) | float }}"

- name: Fail promotion when model accuracy is below threshold
  ansible.builtin.fail:
    msg: >-
      Automated gate failed: model {{ azure_ml_menv_model_name }}:{{ azure_ml_menv_model_version }}
      accuracy {{ _gate_accuracy }} is below required {{ azure_ml_menv_min_accuracy }}
  when: _gate_accuracy | float < azure_ml_menv_min_accuracy | float

- name: Record automated gate as passed
  ansible.builtin.set_fact:
    _menv_gate_result: passed

- name: Fail promotion when manual approval is required but not granted
  ansible.builtin.fail:
    msg: >-
      Approval gate failed: promotion to {{ gate_target_env }} requires approval.
      Set azure_ml_menv_promotion_approved=true (supplied by the AAP approval node).
  when:
    - _gate_target_cfg.requires_approval | bool
    - not (azure_ml_menv_promotion_approved | bool)

- name: Record approval status
  ansible.builtin.set_fact:
    _menv_approval_status: "{{ 'approved' if _gate_target_cfg.requires_approval | bool else 'not_required' }}"
```

- [ ] **Step 2: Validate**

Run: `yamllint roles/multi_env_ml_deployment/tasks/validate_promotion_gate.yml`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add roles/multi_env_ml_deployment/tasks/validate_promotion_gate.yml
git commit -m "feat: add promotion validation + approval gate to multi_env_ml_deployment"
```

---

## Task 6: Model promotion (`promote_model.yml`)

**Files:**
- Create: `roles/multi_env_ml_deployment/tasks/promote_model.yml`

**Interfaces:**
- Consumes (task/role vars): `azure_ml_menv_promote_source` (str, e.g. `dev`), `azure_ml_menv_promote_target` (str, e.g. `staging`), model vars, `azure_ml_menv_use_registry`.
- Produces: the model version registered in the target workspace (reliable path); best-effort publish to the shared ML registry; a `promote` audit record capturing gate + approval result.

- [ ] **Step 1: Write `promote_model.yml`**

```yaml
---
- name: Run promotion gates ({{ azure_ml_menv_promote_source }} -> {{ azure_ml_menv_promote_target }})
  ansible.builtin.include_tasks: validate_promotion_gate.yml
  vars:
    gate_source_env: "{{ azure_ml_menv_promote_source }}"
    gate_target_env: "{{ azure_ml_menv_promote_target }}"

- name: Resolve source and target workspace names
  ansible.builtin.set_fact:
    _promote_source_ws: "{{ azure_resource_group[:22] }}-ml-{{ azure_ml_menv_environments[azure_ml_menv_promote_source].code }}"
    _promote_target_ws: "{{ azure_resource_group[:22] }}-ml-{{ azure_ml_menv_environments[azure_ml_menv_promote_target].code }}"

- name: Create local model artifact for promotion
  ansible.builtin.tempfile:
    state: directory
    prefix: menv_promote_
  register: _promote_tmpdir

- name: Write promoted model file
  ansible.builtin.copy:
    dest: "{{ _promote_tmpdir.path }}/model.json"
    content: '{"framework": "dummy", "accuracy": 0.95}'
    mode: "0644"

- name: Register promoted model in target workspace {{ azure_ml_menv_promote_target }}
  azure.azcollection.azure_rm_ml_model:
    resource_group: "{{ azure_resource_group }}"
    ml_workspace: "{{ _promote_target_ws }}"
    name: "{{ azure_ml_menv_model_name }}"
    version: "{{ azure_ml_menv_model_version }}"
    resource_definition: |
      type: custom_model
      path: {{ _promote_tmpdir.path }}
      description: Model promoted from {{ azure_ml_menv_promote_source }} to {{ azure_ml_menv_promote_target }}
      tags:
        accuracy: "0.95"
        promoted_from: {{ azure_ml_menv_promote_source }}

- name: Publish promoted model to shared ML registry (best-effort)
  when: azure_ml_menv_use_registry | bool
  block:
    - name: Upload promoted model to ML registry
      azure.azcollection.azure_rm_ml_model:
        ml_registry: "{{ azure_ml_menv_registry_name }}"
        name: "{{ azure_ml_menv_model_name }}"
        version: "{{ azure_ml_menv_model_version }}"
        resource_definition: |
          type: custom_model
          path: {{ _promote_tmpdir.path }}
          description: Shared model promoted to {{ azure_ml_menv_promote_target }}
  rescue:
    - name: Warn that registry publish requires additional permissions
      ansible.builtin.debug:
        msg: >-
          Registry publish skipped (authorization error). Ensure the identity has
          Storage Blob Data Contributor on the ML registry backing storage.
  always:
    - name: Clean up promotion artifact directory
      ansible.builtin.file:
        path: "{{ _promote_tmpdir.path | default('/nonexistent') }}"
        state: absent
      when: _promote_tmpdir.path is defined

- name: Record promotion in the audit trail
  ansible.builtin.include_tasks: record_audit_event.yml
  vars:
    audit_action: promote
    audit_environment: "{{ azure_ml_menv_promote_target }}"
    audit_model_name: "{{ azure_ml_menv_model_name }}"
    audit_model_version: "{{ azure_ml_menv_model_version }}"
    audit_approval_status: "{{ _menv_approval_status }}"
    audit_gate_result: "{{ _menv_gate_result }}"
```

- [ ] **Step 2: Validate**

Run: `yamllint roles/multi_env_ml_deployment/tasks/promote_model.yml`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add roles/multi_env_ml_deployment/tasks/promote_model.yml
git commit -m "feat: add gated model promotion with audit to multi_env_ml_deployment"
```

---

## Task 7: Teardown (`delete_environment.yml`, `delete_shared_infrastructure.yml`)

**Files:**
- Create: `roles/multi_env_ml_deployment/tasks/delete_environment.yml`
- Create: `roles/multi_env_ml_deployment/tasks/delete_shared_infrastructure.yml`

**Interfaces:**
- Consumes: same name vars. Produces: best-effort teardown; `delete_shared_infrastructure` deletes the resource group last.

- [ ] **Step 1: Write `delete_environment.yml`**

```yaml
---
- name: Delete compute cluster in environment {{ azure_ml_menv_environment }}
  azure.azcollection.azure_rm_ml_compute:
    resource_group: "{{ azure_resource_group }}"
    ml_workspace: "{{ azure_ml_menv_workspace_name }}"
    name: "{{ azure_ml_menv_compute_name }}"
    state: absent
  failed_when: false

- name: Delete ML workspace for environment {{ azure_ml_menv_environment }}
  azure.azcollection.azure_rm_ml_workspace:
    resource_group: "{{ azure_resource_group }}"
    name: "{{ azure_ml_menv_workspace_name }}"
    state: absent
  failed_when: false

- name: Delete environment storage account
  ansible.builtin.include_role:
    name: cloud.azure_ops.azure_manage_storage_account
  vars:
    azure_manage_storage_account_operation: delete
    azure_manage_storage_account_name: "{{ azure_ml_menv_storage_account }}"
    azure_manage_storage_account_resource_group: "{{ azure_resource_group }}"

- name: Record environment deletion in the audit trail
  ansible.builtin.include_tasks: record_audit_event.yml
  vars:
    audit_action: delete
    audit_environment: "{{ azure_ml_menv_environment }}"
  failed_when: false
```

- [ ] **Step 2: Write `delete_shared_infrastructure.yml`**

```yaml
---
- name: Delete ML registry
  azure.azcollection.azure_rm_ml_registry:
    resource_group: "{{ azure_resource_group }}"
    name: "{{ azure_ml_menv_registry_name }}"
    state: absent
  failed_when: false
  when: azure_ml_menv_use_registry | bool

- name: Delete shared Container Registry
  azure.azcollection.azure_rm_containerregistry:
    resource_group: "{{ azure_resource_group }}"
    name: "{{ azure_ml_menv_acr_name }}"
    state: absent
  failed_when: false

- name: Delete shared Application Insights
  azure.azcollection.azure_rm_resource:
    resource_group: "{{ azure_resource_group }}"
    provider: Insights
    resource_type: components
    resource_name: "{{ azure_ml_menv_appinsights_name }}"
    api_version: "2020-02-02"
    state: absent
  failed_when: false

- name: Delete shared Key Vault
  azure.azcollection.azure_rm_keyvault:
    resource_group: "{{ azure_resource_group }}"
    vault_name: "{{ azure_ml_menv_keyvault_name }}"
    state: absent
  failed_when: false

- name: Delete audit storage account
  ansible.builtin.include_role:
    name: cloud.azure_ops.azure_manage_storage_account
  vars:
    azure_manage_storage_account_operation: delete
    azure_manage_storage_account_name: "{{ azure_ml_menv_audit_storage_account }}"
    azure_manage_storage_account_resource_group: "{{ azure_resource_group }}"

- name: Delete resource group
  ansible.builtin.include_role:
    name: cloud.azure_ops.azure_manage_resource_group
  vars:
    azure_manage_resource_group_operation: delete
    azure_manage_resource_group_name: "{{ azure_resource_group }}"
    azure_manage_resource_group_force_delete_nonempty: true
```

- [ ] **Step 3: Validate**

Run: `yamllint roles/multi_env_ml_deployment/tasks/delete_environment.yml roles/multi_env_ml_deployment/tasks/delete_shared_infrastructure.yml`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add roles/multi_env_ml_deployment/tasks/delete_environment.yml roles/multi_env_ml_deployment/tasks/delete_shared_infrastructure.yml
git commit -m "feat: add teardown operations to multi_env_ml_deployment"
```

---

## Task 8: Example orchestration playbook + vars

**Files:**
- Create: `playbooks/multi_env_ml_deployment.yml`
- Create: `playbooks/vars/multi_env_ml_deployment_vars.yml`

**Interfaces:**
- Consumes: the role. Produces: a runnable end-to-end demonstration of provision → per-env provision → dev model registration → gated promotion dev→staging→prod.

- [ ] **Step 1: Write `playbooks/vars/multi_env_ml_deployment_vars.yml`** — copy the "Reference variable model" block (Task 1), minus `operation`/`azure_ml_menv_environment` (the playbook sets those per call). This lets `--syntax-check` and CLI runs resolve names.

- [ ] **Step 2: Write `playbooks/multi_env_ml_deployment.yml`**

```yaml
---
- name: Multi-environment Azure ML deployment with AAP-style promotion
  hosts: localhost
  gather_facts: false

  vars_files:
    - vars/multi_env_ml_deployment_vars.yml

  tasks:
    - name: Fail when azure_resource_group is not defined
      ansible.builtin.fail:
        msg: azure_resource_group must be defined
      when: azure_resource_group is not defined

    - name: Provision shared hub infrastructure
      ansible.builtin.include_role:
        name: cloud.azure_ops.multi_env_ml_deployment
      vars:
        operation: provision_shared_infrastructure

    - name: Provision each environment (dev, staging, prod)
      ansible.builtin.include_role:
        name: cloud.azure_ops.multi_env_ml_deployment
      vars:
        operation: provision_environment
        azure_ml_menv_environment: "{{ _env_item }}"
      loop:
        - dev
        - staging
        - prod
      loop_control:
        loop_var: _env_item

    - name: Register initial model version in dev workspace
      azure.azcollection.azure_rm_ml_model:
        resource_group: "{{ azure_resource_group }}"
        ml_workspace: "{{ azure_resource_group[:22] }}-ml-dev"
        name: "{{ azure_ml_menv_model_name }}"
        version: "{{ azure_ml_menv_model_version }}"
        resource_definition: |
          type: custom_model
          path: azureml://datastores/workspaceblobstore/paths/model
          tags:
            accuracy: "0.95"
      # NOTE: for a real run, replace path with a trained model artifact.

    - name: Promote model dev -> staging
      ansible.builtin.include_role:
        name: cloud.azure_ops.multi_env_ml_deployment
      vars:
        operation: promote_model
        azure_ml_menv_promote_source: dev
        azure_ml_menv_promote_target: staging

    - name: Promote model staging -> prod
      ansible.builtin.include_role:
        name: cloud.azure_ops.multi_env_ml_deployment
      vars:
        operation: promote_model
        azure_ml_menv_promote_source: staging
        azure_ml_menv_promote_target: prod
```

- [ ] **Step 3: Validate syntax**

Run: `ansible-playbook --syntax-check playbooks/multi_env_ml_deployment.yml -e azure_resource_group=synbox` (from a checkout with `azure.azcollection` + this collection on the path)
Expected: playbook parses (no template/syntax errors). If the collection isn't installed locally, run `yamllint` on both files instead and note syntax-check runs in CI.

- [ ] **Step 4: Commit**

```bash
git add playbooks/multi_env_ml_deployment.yml playbooks/vars/multi_env_ml_deployment_vars.yml
git commit -m "feat: add multi_env_ml_deployment example playbook and vars"
```

---

## Task 9: Documentation (playbook doc + AAP workflow doc)

**Files:**
- Create: `playbooks/MULTI_ENV_ML_DEPLOYMENT.md`
- Create: `docs/aap_surveys/multi_env_ml_workflow.md`

**Interfaces:** none (docs). Produces: architecture diagram, promotion-flow, gates, audit, network-isolation sections, runbook; AAP workflow node graph + survey.

- [ ] **Step 1: Write `playbooks/MULTI_ENV_ML_DEPLOYMENT.md`** modeled on `playbooks/MLOPS_LIFECYCLE.md`. Required sections:
  - Overview + when to use.
  - **Architecture diagram** (ASCII) showing hub (RG, Registry, KV, ACR, App Insights, audit storage) and three spokes (dev/staging/prod workspaces + storage + compute), with the promotion arrows dev→staging→prod through the registry.
  - **Promotion flow** with the two gates between each hop.
  - **Environment configuration** table documenting `azure_ml_menv_environments` fields.
  - **Gates** section: automated (`azure_ml_menv_min_accuracy`) + approval (`azure_ml_menv_promotion_approved`), and how AAP supplies the approval.
  - **Audit trail** section: blob naming, record fields, immutability rationale.
  - **Network isolation** section: per-env `public_network_access`, plus the documented private-endpoint / VNet-peering / private-DNS pattern for staging/prod (guidance, not provisioned).
  - **Runbook**: CLI invocations per operation and the full-cycle example; teardown.

- [ ] **Step 2: Write `docs/aap_surveys/multi_env_ml_workflow.md`** modeled on `docs/aap_surveys/workflow_templates.md`. Include: the workflow node graph (provision-shared → provision-dev/staging/prod → register-dev-model → automated-gate → **approval node** → promote-staging → automated-gate → **approval node** → promote-prod), and a survey spec exposing `azure_ml_menv_min_accuracy` and `azure_ml_menv_promotion_approved`.

- [ ] **Step 3: Validate**

Run: `yamllint docs/aap_surveys/multi_env_ml_workflow.md || true` (markdown; yamllint may skip) and visually confirm the diagram renders.

- [ ] **Step 4: Commit**

```bash
git add playbooks/MULTI_ENV_ML_DEPLOYMENT.md docs/aap_surveys/multi_env_ml_workflow.md
git commit -m "docs: add multi_env_ml_deployment architecture and AAP workflow docs"
```

---

## Task 10: Integration test target

**Files:**
- Create: `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/aliases`
- Create: `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/defaults/main.yml`
- Create: `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/tasks/main.yml`
- Create: `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/tasks/create_and_validate.yml`
- Create: `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/tasks/teardown.yml`

**Interfaces:**
- Consumes: `resource_prefix` (from azure ansible-test plugin) and the role. Produces: a self-contained live-Azure test of the full promotion cycle + audit assertions.

- [ ] **Step 1: Write `aliases`**

```
cloud/azure
playbook/multi_env_ml_deployment
time=45m
```

- [ ] **Step 2: Write `defaults/main.yml`** (lightweight compute; distinct test var names to avoid recursion):

```yaml
---
test_azure_resource_group: "{{ resource_prefix }}-mlmenv"
test_azure_region: eastus
test_azure_ml_menv_compute_vm_size: Standard_DS2_v2
```

- [ ] **Step 3: Write `tasks/main.yml`**

```yaml
---
- name: Test multi-environment ML deployment
  block:
    - name: Run create-and-validate flow
      ansible.builtin.include_tasks: create_and_validate.yml
  always:
    - name: Tear down all multi-env ML resources
      ansible.builtin.include_tasks: teardown.yml
```

- [ ] **Step 4: Write `tasks/create_and_validate.yml`** — provision shared + 3 envs, register a dev model with `accuracy: "0.95"`, promote through both gates with approval granted, then assert audit blobs exist. Pass `azure_region: "{{ test_azure_region }}"` (NOT self-referential) and override compute size:

```yaml
---
- name: Provision shared hub infrastructure
  ansible.builtin.include_role:
    name: cloud.azure_ops.multi_env_ml_deployment
  vars:
    operation: provision_shared_infrastructure
    azure_resource_group: "{{ test_azure_resource_group }}"
    azure_region: "{{ test_azure_region }}"

- name: Provision each environment
  ansible.builtin.include_role:
    name: cloud.azure_ops.multi_env_ml_deployment
  vars:
    operation: provision_environment
    azure_resource_group: "{{ test_azure_resource_group }}"
    azure_region: "{{ test_azure_region }}"
    azure_ml_menv_environment: "{{ _env_item }}"
    azure_ml_menv_compute_vm_size: "{{ test_azure_ml_menv_compute_vm_size }}"
  loop:
    - dev
    - staging
    - prod
  loop_control:
    loop_var: _env_item

- name: Register initial model version in dev workspace
  azure.azcollection.azure_rm_ml_model:
    resource_group: "{{ test_azure_resource_group }}"
    ml_workspace: "{{ test_azure_resource_group[:22] }}-ml-dev"
    name: menv-model
    version: "1"
    resource_definition: |
      type: custom_model
      path: azureml://datastores/workspaceblobstore/paths/model
      tags:
        accuracy: "0.95"

- name: Promote dev -> staging (approval granted)
  ansible.builtin.include_role:
    name: cloud.azure_ops.multi_env_ml_deployment
  vars:
    operation: promote_model
    azure_resource_group: "{{ test_azure_resource_group }}"
    azure_region: "{{ test_azure_region }}"
    azure_ml_menv_promote_source: dev
    azure_ml_menv_promote_target: staging
    azure_ml_menv_promotion_approved: true

- name: Promote staging -> prod (approval granted)
  ansible.builtin.include_role:
    name: cloud.azure_ops.multi_env_ml_deployment
  vars:
    operation: promote_model
    azure_resource_group: "{{ test_azure_resource_group }}"
    azure_region: "{{ test_azure_region }}"
    azure_ml_menv_promote_source: staging
    azure_ml_menv_promote_target: prod
    azure_ml_menv_promotion_approved: true

- name: List audit blobs
  azure.azcollection.azure_rm_storageblob_info:
    resource_group: "{{ test_azure_resource_group }}"
    storage_account_name: "{{ (test_azure_resource_group | regex_replace('[^a-z0-9]', ''))[:15] }}auditml"
    container: audit
  register: _audit_blobs

- name: Assert promotion audit records were written
  ansible.builtin.assert:
    that:
      - _audit_blobs.blobs | selectattr('name', 'search', 'promote') | list | length >= 2
    fail_msg: Expected at least two 'promote' audit records
    success_msg: Audit trail captured the promotion events
```

- [ ] **Step 5: Write `tasks/teardown.yml`**

```yaml
---
- name: Delete each environment
  ansible.builtin.include_role:
    name: cloud.azure_ops.multi_env_ml_deployment
  vars:
    operation: delete_environment
    azure_resource_group: "{{ test_azure_resource_group }}"
    azure_ml_menv_environment: "{{ _env_item }}"
  loop:
    - dev
    - staging
    - prod
  loop_control:
    loop_var: _env_item
  failed_when: false

- name: Delete shared infrastructure and resource group
  ansible.builtin.include_role:
    name: cloud.azure_ops.multi_env_ml_deployment
  vars:
    operation: delete_shared_infrastructure
    azure_resource_group: "{{ test_azure_resource_group }}"
  failed_when: false
```

- [ ] **Step 6: Validate**

Run: `yamllint tests/integration/targets/azure_ops_test_multi_env_ml_deployment/`
Expected: no errors. (Live run happens in CI.)

- [ ] **Step 7: Commit**

```bash
git add tests/integration/targets/azure_ops_test_multi_env_ml_deployment
git commit -m "test: add integration test for multi_env_ml_deployment (ACA-5889)"
```

---

## Task 11: Wire-up (README row + galaxy version)

**Files:**
- Modify: `README.md:40-41` (add row before `<!--end collection content-->`)
- Modify: `galaxy.yml:4`

**Interfaces:** none. Produces: discoverable, versioned release.

- [ ] **Step 1: Add the README playbook row** after the `self_service_ml_platform` row (line 40):

```
[cloud.azure_ops.multi_env_ml_deployment](https://github.com/redhat-cop/cloud.azure_ops/blob/main/playbooks/MULTI_ENV_ML_DEPLOYMENT.md)|A playbook to deploy Azure ML across dev/staging/production with AAP-orchestrated model promotion, approval and validation gates, an immutable audit trail, and per-environment network isolation.
```

- [ ] **Step 2: Bump `galaxy.yml` version** `6.1.2` → `6.2.0`.

- [ ] **Step 3: Validate**

Run: `yamllint galaxy.yml`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add README.md galaxy.yml
git commit -m "docs: register multi_env_ml_deployment playbook and bump to 6.2.0"
```

---

## Self-Review

**Spec coverage:**
- Multi-env architecture + AAP orchestration → Tasks 3, 4, 8, 9.
- Model promotion w/ approval gates + automated validation → Tasks 5, 6.
- Environment-specific variable management → `azure_ml_menv_environments` (Tasks 1, 4).
- ML Registry cross-env sharing → Tasks 3, 6 (best-effort publish).
- Audit trail + compliance evidence → Tasks 2, 6 (records on every action); asserted in Task 10.
- Network isolation per env → Task 4 (`public_network_access`) + Task 9 (documented patterns).
- Full promotion cycle tested → Task 10.
- Architecture diagram / runbook → Task 9.
- README + version → Task 11.

**Placeholder scan:** every code step contains concrete content; the one `NOTE` in Task 8 documents a deliberate demo shortcut (dummy model path), not a gap.

**Type/name consistency:** operation names match task-file basenames; `azure_ml_menv_*` variable names are consistent across defaults, tasks, playbook, and test; workspace-name derivation `"{{ azure_resource_group[:22] }}-ml-{{ code }}"` is identical in provision, gate, promote, and test; audit storage name derivation `[:15] ~ 'auditml'` is identical in Task 1, Task 2, and Task 10.
