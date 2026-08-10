# Service Reference

Red Queen RC1 registers **66** services under the technical `wnhf` domain. Classification is taken from the RC1 `ReleaseProfile` source.

## Stable public

### `wnhf.system_status`

**Get Red Queen system status**

Returns the aggregated read-only runtime, registry, validation, execution and runtime-readiness status.

No input fields.

### `wnhf.release_scope`

**Get Red Queen release scope**

Returns active and planned domains for the current release-candidate baseline.

No input fields.

### `wnhf.release_info`

**Get release information**

Returns framework version, release-candidate phase, scope and compatibility metadata.

No input fields.

### `wnhf.public_api`

**Get public API registry**

Returns stable, diagnostic, maintenance and legacy service classifications.

No input fields.

### `wnhf.qualification`

**Get framework qualification**

Returns runtime readiness plus canonical persistent execution-evidence qualification for the current baseline.

No input fields.

### `wnhf.upgrade_check`

**Check upgrade compatibility**

Returns current compatibility, migration and installation requirements.

No input fields.

### `wnhf.execution_dry_run`

**Build semantic execution dry-run**

Validates a semantic execution request and builds a complete execution plan without dispatching hardware commands.

| Field | Required | Default | Description |
|---|---:|---|---|
| `action_id` | yes | `—` | Stable semantic action ID. |
| `target` | yes | `—` | Canonical semantic target map. The current lighting.turn_off contract requires exactly one object_id. |
| `parameters` | no | `—` | Generic action parameter map. |
| `confirmed` | no | `False` | Explicit confirmation context for actions that require it. |

### `wnhf.execution_execute`

**Execute canonical semantic action**

Canonical Red Queen real-execution entry. Currently lighting.turn_off is enabled and targets exactly one semantic light object.

| Field | Required | Default | Description |
|---|---:|---|---|
| `action_id` | yes | `—` | Stable semantic action ID. The current real-execution surface enables lighting.turn_off. |
| `target` | yes | `—` | Canonical semantic target map. lighting.turn_off requires exactly one object_id. |
| `parameters` | no | `—` | Action parameters. Must be empty for the current lighting.turn_off contract. |
| `confirmed` | no | `False` | Explicit confirmation context when required by an action. |

## Diagnostic public

### `wnhf.validate_registry`

**Validate framework**

Runs non-destructive Red Queen registry, entity, duplicate and runtime checks.

No input fields.

### `wnhf.house_snapshot`

**Get house snapshot**

Returns the current aggregated Red Queen state of the complete house.

No input fields.

### `wnhf.capabilities_snapshot`

**Get capabilities snapshot**

Returns all registered Red Queen capabilities and provider states.

No input fields.

### `wnhf.rules_snapshot`

**Get rules snapshot**

Returns loaded rules, warnings, facts and the current evaluation.

No input fields.

### `wnhf.context_snapshot`

**Get context snapshot**

Returns the current semantic Red Queen context with reasons and scores.

No input fields.

### `wnhf.policies_snapshot`

**Get policies snapshot**

Returns policy mode, configuration and current calculated decisions.

No input fields.

### `wnhf.decisions_snapshot`

**Get decisions snapshot**

Returns all configured read-only decisions for the current context.

No input fields.

### `wnhf.registry_recovery_report`

**Get registry recovery report**

Checks required registry files and reports safe-mode status.

No input fields.

### `wnhf.executions_snapshot`

**Get execution plans snapshot**

Builds dry-run plans for all configured Decisions.

No input fields.

### `wnhf.execution_audit`

**Get execution audit**

Returns the bounded in-memory audit of explicit execution attempts.

No input fields.

### `wnhf.execution_capabilities_snapshot`

**Get execution capabilities**

Resolves hardware-neutral turn-off strategies for all registered lights.

No input fields.

### `wnhf.real_step_audit`

**Get real-step audit**

Returns the bounded in-memory audit of Stage-3.2 real-step attempts.

No input fields.

### `wnhf.sequential_room_audit`

**Get sequential room audit**

Returns the bounded in-memory audit of Stage-3.3 room transactions.

No input fields.

### `wnhf.house_execution_audit`

**Get house execution audit**

Returns the bounded in-memory audit of Stage-3.4 house transactions.

No input fields.

### `wnhf.transaction_locks`

**Get transaction locks**

Returns active execution scope locks and the latest lock decision.

No input fields.

### `wnhf.transaction_queue`

**Get transaction queue**

Returns the active FIFO scheduler queue and current locks.

No input fields.

### `wnhf.access_snapshot`

**Get Access runtime snapshot**

Returns normalized read-only states for windows, sliding doors, doors, locks and garage doors.

No input fields.

### `wnhf.object_capabilities_snapshot`

**Get object capability contracts**

Returns the semantic capability catalog and all Lighting and Access object declarations.

No input fields.

### `wnhf.access_execution_audit`

**Get Access execution audit**

Returns the bounded in-memory audit of Access object execution attempts.

No input fields.

### `wnhf.access_result_catalog`

**Get Access result catalog**

Returns the stable machine-readable Access execution result and error codes.

No input fields.

### `wnhf.provider_qualification`

**Get provider qualification**

Returns installation-neutral provider qualification derived from canonical semantic execution evidence.

No input fields.

### `wnhf.provider_contract`

**Get provider contract diagnostics**

Validates registered providers against the stable Red Queen provider contract without changing runtime behavior.

No input fields.

### `wnhf.provider_registry`

**Get provider registry diagnostics**

Returns provider-centric registration, capability indexes and deterministic provider resolution.

No input fields.

### `wnhf.provider_discovery`

**Get provider discovery diagnostics**

Returns scanned modules, discovered providers and non-fatal discovery issues.

No input fields.

### `wnhf.provider_diagnostics`

**Get unified provider diagnostics**

Returns identity, runtime, contract, registry, discovery, qualification, confidence, capabilities and recommendations for every provider.

No input fields.

### `wnhf.capability_registry`

**Get capability registry diagnostics**

Returns semantic capability definitions, contract validation and current provider bindings.

No input fields.

### `wnhf.capability_resolver`

**Get capability resolver diagnostics**

Resolves semantic capabilities to selected providers and returns runtime health and selection reasons.

No input fields.

### `wnhf.capability_manager`

**Get capability manager status**

Returns aggregate status for the public read-only semantic capability layer.

No input fields.

### `wnhf.capability_list`

**List semantic capabilities**

Returns a compact list of all registered semantic capabilities and their current resolution state.

No input fields.

### `wnhf.capability_info`

**Get semantic capability information**

Returns the complete definition, resolution and diagnostics for one semantic capability.

| Field | Required | Default | Description |
|---|---:|---|---|
| `capability_id` | yes | `—` | Stable semantic capability ID, for example lighting. |

### `wnhf.execution_manager`

**Get generic execution manager status**

Returns the semantic action catalog and read-only execution readiness through the Capability Manager.

No input fields.

### `wnhf.execution_action`

**Resolve semantic execution action**

Resolves one semantic action through the Capability Manager without executing hardware commands.

| Field | Required | Default | Description |
|---|---:|---|---|
| `action_id` | yes | `—` | Stable semantic action ID, for example lighting.turn_off. |

### `wnhf.execution_qualification`

**Get generic execution qualification**

Returns the generic execution evidence architecture, store state and current qualification report.

No input fields.

### `wnhf.execution_runtime_health`

**Get generic execution runtime health**

Returns aggregate health for the execution manager, semantic router, providers and qualification persistence.

No input fields.

## Maintenance public

### `wnhf.reload_registry`

**Reload registry**

Reloads and validates rooms.yaml and lights.yaml without restarting Home Assistant.

No input fields.

### `wnhf.reload_rules`

**Reload rules**

Reloads YAML rules and returns a fresh evaluation.

No input fields.

### `wnhf.reload_policies`

**Reload policies**

Reloads optional policy YAML files without restarting Home Assistant.

No input fields.

### `wnhf.reload_decisions`

**Reload decisions**

Reloads optional decision YAML files without restarting Home Assistant.

No input fields.

## Legacy / development

### `wnhf.lighting_all_off`

**Lighting – All off**

Switches off every controllable Red Queen light currently reporting on.

No input fields.

**Policy:** not recommended for new automations.

### `wnhf.lighting_room_off`

**Lighting – Room off**

Switches off every controllable light in one Red Queen room.

| Field | Required | Default | Description |
|---|---:|---|---|
| `room_id` | yes | `—` | Stable room ID, for example house.eg.kitchen. |

**Policy:** not recommended for new automations.

### `wnhf.lighting_object_off`

**Lighting – Object off**

Switches off one Red Queen light object if its feedback currently reports on.

| Field | Required | Default | Description |
|---|---:|---|---|
| `light_id` | yes | `—` | Stable light ID, for example light.eg.office.main. |

**Policy:** not recommended for new automations.

### `wnhf.list_registry`

**Registry – List objects**

Lists objects from one supported Red Queen registry type.

| Field | Required | Default | Description |
|---|---:|---|---|
| `type` | yes | `—` | Registry collection to return. |

**Policy:** not recommended for new automations.

### `wnhf.get_object`

**Registry – Get object**

Returns one Red Queen registry object by its stable ID.

| Field | Required | Default | Description |
|---|---:|---|---|
| `id` | yes | `—` | Stable Red Queen ID, such as house.eg.office or light.eg.office.main. |

**Policy:** not recommended for new automations.

### `wnhf.evaluate_rules`

**Evaluate rules**

Evaluates all enabled Red Queen rules against current house facts.

No input fields.

**Policy:** not recommended for new automations.

### `wnhf.policy_check`

**Check policy**

Checks whether one semantic action is currently allowed.

| Field | Required | Default | Description |
|---|---:|---|---|
| `policy_id` | yes | `—` | Semantic permission ID, for example announcements.play. |

**Policy:** not recommended for new automations.

### `wnhf.decision_evaluate`

**Evaluate decision**

Evaluates one read-only semantic decision.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | Semantic decision ID, for example lighting.house_all_off. |

**Policy:** not recommended for new automations.

### `wnhf.execution_plan`

**Build execution plan**

Builds a validated dry-run plan for one Decision without executing it.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | Semantic Decision ID to plan. |

**Policy:** not recommended for new automations.

### `wnhf.execution_commit`

**Commit execution transaction**

Executes one explicitly confirmed Stage-1 lighting.object_off Decision.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | Decision using lighting.object_off and one light_id target. |
| `confirm` | yes | `—` | Must be true before a real command can be sent. |

**Policy:** not recommended for new automations.

### `wnhf.execute`

**Execute legacy Red Queen Decision**

Legacy Decision-ID execution entry retained for compatibility. New automations should use execution_execute.

| Field | Required | Default | Description |
|---|---:|---|---|
| `id` | yes | `—` | Semantic Decision ID. |
| `confirm` | yes | `—` | Must be true before an active command can be sent. |
| `conflict_policy` | no | `reject` | Reject immediately or wait in the FIFO scheduler queue. |
| `queue_timeout` | no | `15` | Maximum wait time in seconds when conflict_policy is wait. |

**Policy:** not recommended for new automations.

### `wnhf.multi_step_plan`

**Build multi-step plan**

Builds a deterministic Stage-2.1 blueprint for room or house lighting off.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | Decision using lighting.room_off or lighting.all_off. |

**Policy:** not recommended for new automations.

### `wnhf.multi_step_simulate`

**Simulate multi-step transaction**

Runs the Stage-2.2 transaction state machine without sending commands.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | Decision using lighting.room_off or lighting.all_off. |
| `confirm` | yes | `—` | Confirms that the transaction should be simulated as a commit. |

**Policy:** not recommended for new automations.

### `wnhf.multi_step_simulations_snapshot`

**Get multi-step simulations**

Returns the bounded in-memory audit of multi-step simulations.

No input fields.

**Policy:** not recommended for new automations.

### `wnhf.generic_transaction_run`

**Run generic transaction**

Runs the Stage-3.1 generic dry-run transaction state machine.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` |  |
| `confirm` | yes | `—` |  |

**Policy:** not recommended for new automations.

### `wnhf.generic_transactions_snapshot`

**Get generic transactions**

Returns the in-memory Stage-3.1 transaction audit.

No input fields.

**Policy:** not recommended for new automations.

### `wnhf.real_step_execute`

**Execute one real transaction step**

Executes exactly one guarded Stage-3.2 blueprint step and verifies feedback.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | A lighting.room_off Decision producing exactly one active step. |
| `confirm` | yes | `—` | Must be true before the real command can be dispatched. |

**Policy:** not recommended for new automations.

### `wnhf.sequential_room_execute`

**Execute room sequentially**

Executes every active lighting.room_off step strictly sequentially with feedback verification.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | A lighting.room_off Decision with one or more active steps. |
| `confirm` | yes | `—` | Must be true before any real command can be dispatched. |

**Policy:** not recommended for new automations.

### `wnhf.house_execute`

**Execute house all off**

Executes a lighting.all_off Decision room by room through the shared Stage-3.4 pipeline.

| Field | Required | Default | Description |
|---|---:|---|---|
| `decision_id` | yes | `—` | A lighting.all_off Decision. |
| `confirm` | yes | `—` | Must be true before any real house command can be dispatched. |

**Policy:** not recommended for new automations.

### `wnhf.access_object_execute`

**Execute one Access object capability**

Executes one tightly constrained and explicitly confirmed Access capability. WP-4.3.2B.5.1 permits access.lock, access.unlock, access.door_open and access.toggle.

| Field | Required | Default | Description |
|---|---:|---|---|
| `object_id` | yes | `—` | Semantic Registry ID of one configured door. |
| `capability_id` | yes | `—` | Must be access.lock, access.unlock, access.door_open or access.toggle in this qualification stage. |
| `confirm` | yes | `—` | Must be true before any real command can be dispatched. |

**Policy:** not recommended for new automations.

## Completeness

- service definitions: `66`
- classified services: `66`
- expected RC1 runtime classification: `66/66`, no duplicates.
