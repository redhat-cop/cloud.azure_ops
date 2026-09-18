# Multi-Environment Azure ML Deployment with AAP — Design

- **Jira:** ACA-5889
- **Date:** 2026-09-18
- **Status:** Approved for planning

## Summary

A reference architecture demonstrating how Ansible Automation Platform (AAP)
manages Azure Machine Learning workloads across three environments —
**dev / staging / production** — with a governed model-promotion pipeline,
approval and automated-validation gates, an immutable audit trail, and
per-environment network isolation.

It builds on the existing `mlops_lifecycle` playbook (dev→prod blue/green) but
generalizes to a three-environment promotion pipeline packaged as a **reusable
role** invoked from an example playbook, following the `self_service_ml_platform`
pattern already in this collection.

## Goals (from the ticket)

- Enterprise ML governance across dev/staging/prod with consistent policies and
  promotion workflows.
- Reduced deployment risk via validated promotion patterns with automated
  testing gates and approval gates.
- Auditable, repeatable ML deployments that support regulated industries.

### In scope

- Multi-environment architecture (dev/staging/production) with AAP orchestration.
- Model promotion workflow with approval gates and automated validation.
- Environment-specific variable management with a single role.
- ML Registry for cross-environment model sharing.
- Audit-trail and compliance-evidence automation.
- Network-isolation patterns per environment.

### Out of scope

- Specific regulatory-framework compliance checklists.
- Multi-cloud deployment patterns.
- Custom approval-workflow UI (approval is modeled as a gate variable supplied by
  an AAP manual-approval node).

## Architecture

### Components

A single role **`multi_env_ml_deployment`** with an operation router in
`tasks/main.yml`, plus a readable example orchestration playbook
`playbooks/multi_env_ml_deployment.yml` that calls the role once per operation to
demonstrate the full cycle.

Resource topology:

- **Shared (hub) resources** — created once by `provision_shared_infrastructure`:
  - Resource group
  - Shared **ML Registry** (cross-environment model catalog / sharing vehicle)
  - Shared Key Vault, Azure Container Registry (ACR), Application Insights
    (mirrors `mlops_lifecycle`, which shares these across workspaces)
  - Dedicated **audit storage account** + `audit` blob container for the audit
    trail
- **Per-environment (spoke) resources** — created by `provision_environment`,
  once per env:
  - Storage account (per env, for isolation)
  - ML workspace (per env), `public_network_access` set from the env config
  - Compute cluster (scale-to-zero), `max_nodes` from env config

> Note: Key Vault / ACR / App Insights are shared across environments to keep the
> resource count and test runtime manageable, matching `mlops_lifecycle`. The
> `.md` documents that a production hardening step would use per-environment Key
> Vaults; this is called out as guidance, not implemented.

### Role operations (`multi_env_ml_deployment_operation`)

| Operation | Purpose |
|-----------|---------|
| `provision_shared_infrastructure` | RG, ML Registry, shared KV/ACR/App Insights, audit storage + container |
| `provision_environment` | One env's storage + workspace + compute; network access from env config |
| `promote_model` | Run gates, publish/reference model to target env via registry + workspace, write audit record |
| `delete_environment` | Tear down one env's spoke resources |
| `delete_shared_infrastructure` | Tear down hub resources and the resource group |

Shared helper task files (not operations, `include_tasks`-ed by operations):

- `validate_promotion_gate.yml` — automated validation gate.
- `record_audit_event.yml` — writes one immutable audit blob.

### Environment-specific configuration

All per-environment differences are driven by one dict variable. The active
environment is selected with `multi_env_ml_deployment_environment`:

```yaml
multi_env_ml_environments:
  dev:
    public_network_access: Enabled
    compute_max_nodes: 4
    requires_approval: false
  staging:
    public_network_access: Disabled
    compute_max_nodes: 2
    requires_approval: true
  prod:
    public_network_access: Disabled
    compute_max_nodes: 2
    requires_approval: true
```

The role reads `multi_env_ml_environments[multi_env_ml_deployment_environment]`
for the workspace name suffix, network access, compute sizing, and whether
promotion into that environment requires manual approval. This is the "one role,
environment-specific variables" governance story required by the ticket.

## Data flow — promotion pipeline

1. **Provision** shared infra, then dev, staging, prod environments.
2. **Register** a candidate model version in the **dev** workspace, tagged with
   its recorded accuracy (stands in for a training-produced metric).
3. **Promote dev → staging**:
   - `validate_promotion_gate.yml` reads the candidate model's accuracy tag and
     fails if below `multi_env_ml_min_accuracy` (automated gate).
   - If the target env config has `requires_approval: true`, the play fails
     unless `multi_env_ml_promotion_approved` is `true` (the value an AAP manual
     approval node supplies).
   - The model is published to the shared ML Registry (best-effort, see below)
     and registered in the **staging** workspace.
   - `record_audit_event.yml` writes a `promote` audit record.
4. **Promote staging → prod**: same gate + approval flow into the **prod**
   workspace; another audit record is written.

### Promotion mechanism vs. ML Registry

The mechanism the integration test asserts is **workspace-level model
registration** in each target environment (reliable and permission-light). The
shared **ML Registry** is used as the cross-environment catalog and is published
to on a best-effort basis with the required role assignment — registry blob
uploads were observed to be permission-flaky in `mlops_lifecycle`, so the
registry publish is wrapped in a `rescue` that logs guidance and continues.
This satisfies "cross-environment model sharing via ML Registry" while keeping
"full promotion cycle tested end-to-end" solid.

## Gates

- **Automated validation gate** (`validate_promotion_gate.yml`): looks up the
  candidate model version in the source workspace, reads its accuracy tag, and
  `fail`s when `accuracy < multi_env_ml_min_accuracy` (default e.g. `0.90`).
- **Manual approval gate**: for a target env with `requires_approval: true`,
  promotion `fail`s unless `multi_env_ml_promotion_approved | bool` is true.
  Custom UI is out of scope; the boolean is what an AAP manual-approval node
  provides.
- **AAP workflow doc** (`docs/aap_surveys/multi_env_ml_workflow.md`): shows the
  workflow node graph — provision jobs → dev model registration → automated-gate
  job → **manual approval node** → promote-to-staging job → automated-gate job →
  **manual approval node** → promote-to-prod job — plus a survey for the gated
  variables.

Both gates are fully exercisable in CI by setting `multi_env_ml_min_accuracy` and
`multi_env_ml_promotion_approved`.

## Audit trail

`record_audit_event.yml` uploads **one immutable, timestamped JSON blob per
event** to the shared audit container, named `audit/<UTC-timestamp>-<action>.json`.
Each record captures:

- `timestamp` (UTC ISO-8601)
- `action` (`provision_shared` / `provision_environment` / `promote` / `delete`)
- `environment` (target env, when applicable)
- `model_name`, `model_version` (for promotions)
- `actor` — service-principal client id / tenant (from the Azure credentials)
- `approval_status` — `approved` / `not_required`
- `gate_result` — `passed` / `skipped`
- `correlation_id` — a run identifier for grouping records from one execution

Immutable per-event blobs (rather than one appended log) provide tamper-evident,
independently retained evidence, which suits the compliance narrative. All
provision, promote, approval, and delete actions call this task.

## Network isolation

Each environment's workspace sets `public_network_access` from its env config
(dev `Enabled`; staging and prod `Disabled`). The `.md` documents the fuller
private-endpoint / VNet-peering / private-DNS pattern that production would layer
on top; provisioning real private endpoints is left as documented guidance to
keep the integration test runnable within budget.

## Error handling

- Provision tasks are idempotent (create/update semantics of the azcollection
  modules), so re-runs are safe.
- Gate failures use `ansible.builtin.fail` with a clear message so an AAP job
  stops before promoting.
- The registry publish uses `block`/`rescue` and continues on permission errors,
  logging remediation guidance (Storage Blob Data Contributor on the registry's
  backing storage).
- Delete tasks use `failed_when: false` so teardown is best-effort and always
  reaches the resource-group deletion, matching `mlops_lifecycle`.
- The integration test wraps the whole run in `block`/`always` and tears down its
  dedicated resource group in `always:`.

## Testing

Integration test target
`tests/integration/targets/azure_ops_test_multi_env_ml_deployment/` (live Azure,
per collection convention):

- `aliases`: `cloud/azure`, `playbook/multi_env_ml_deployment`, `time=45m`.
- Self-contained: creates a dedicated resource group `{{ resource_prefix }}-mlmenv`,
  uses it, and deletes it in `always:` (never deletes the shared `resource_group`).
- Flow: `provision_shared_infrastructure` → `provision_environment` for dev,
  staging, prod (lightweight compute: `Standard_DS2_v2`, `max_nodes: 1`) →
  register a model in dev with an accuracy tag → `promote_model` dev→staging and
  staging→prod with `multi_env_ml_promotion_approved: true` and a passing
  `multi_env_ml_min_accuracy` → assert the expected audit blobs exist in the audit
  container → (optionally) assert a below-threshold accuracy fails the gate.
- **Skips online endpoints** to keep runtime sane.
- Invokes the role via `include_role` (not inline task copies).
- Uses distinct test variable names (e.g. `test_azure_region`) passed into
  `include_role` to avoid the self-referential-var recursion pitfall.

Local validation without Azure: `yamllint` + `ansible-playbook --syntax-check`
on a wrapper play importing the target's `tasks/main.yml`.

## Files

New:

- `roles/multi_env_ml_deployment/README.md`
- `roles/multi_env_ml_deployment/defaults/main.yml`
- `roles/multi_env_ml_deployment/tasks/main.yml` (router)
- `roles/multi_env_ml_deployment/tasks/provision_shared_infrastructure.yml`
- `roles/multi_env_ml_deployment/tasks/provision_environment.yml`
- `roles/multi_env_ml_deployment/tasks/promote_model.yml`
- `roles/multi_env_ml_deployment/tasks/delete_environment.yml`
- `roles/multi_env_ml_deployment/tasks/delete_shared_infrastructure.yml`
- `roles/multi_env_ml_deployment/tasks/validate_promotion_gate.yml`
- `roles/multi_env_ml_deployment/tasks/record_audit_event.yml`
- `playbooks/multi_env_ml_deployment.yml` (example orchestration)
- `playbooks/MULTI_ENV_ML_DEPLOYMENT.md`
- `playbooks/vars/multi_env_ml_deployment_vars.yml`
- `docs/aap_surveys/multi_env_ml_workflow.md`
- `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/aliases`
- `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/defaults/main.yml`
- `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/tasks/main.yml`
- `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/tasks/create_and_validate.yml`
- `tests/integration/targets/azure_ops_test_multi_env_ml_deployment/tasks/teardown.yml`

Modified:

- `README.md` — add the playbook row.
- `galaxy.yml` — bump `6.1.2` → `6.2.0`.

## Definition of Done mapping

| DoD item | Where satisfied |
|----------|-----------------|
| Multi-environment architecture diagram with promotion flow | `MULTI_ENV_ML_DEPLOYMENT.md` |
| Provisioning handles dev/staging/prod differences | `multi_env_ml_environments` dict + `provision_environment` |
| Promotion workflow includes automated validation gates | `validate_promotion_gate.yml` + approval var |
| Audit trail captures all deployment actions and approvals | `record_audit_event.yml` (immutable blobs) |
| Network isolation patterns documented per environment | per-env `public_network_access` + `.md` patterns |
| Full promotion cycle tested end-to-end | integration test target |
