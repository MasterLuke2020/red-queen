# RC1 Verification Report

## Result

**Red Queen 1.0.0-rc1 — LIVE VERIFIED**

## Verified baseline

- Development baseline: WNHF `1.27.0`
- Work package: `WP-4.7.9.1`
- Public release: Red Queen `1.0.0-rc1`
- RC blocker count at release: `0`

## Pre-release regression gate

Before branding/release packaging the verified baseline passed:

- clean startup;
- execution-manager readiness truth (`5` declared, `5` semantically ready, `1` real execution enabled, `1` executable now);
- runtime health healthy;
- invalid dry-run target (`EXE-203`);
- unknown semantic target (`EXE-203`);
- invalid parameters (`EXE-204`);
- valid dry run (`EXE-100`) without command dispatch;
- idempotent real execution (`EXE-101`) with feedback off and no command;
- canonical last-execution observability;
- config-entry reload with fresh health 100;
- persistent evidence surviving reload;
- real hardware success (`EXE-000`) with feedback ON → command → feedback OFF;
- final system status health 100;
- final qualification pass.

## Final canonical hardware success

Execution ID:

```text
exe_20260809T161726_999223Z_0733606f
```

Result:

```text
state: succeeded
result_code: EXE-000
executed: true
command_sent: true
feedback_confirmed: true
```

Target: `light.eg.kitchen.spots`  
Command entity: `button.btwebeglichtkuechespots`  
Feedback entity: `binary_sensor.qxeglichtkuechespots`

Observed state transition: feedback `on` before dispatch and `off` after dispatch.

## Persistent evidence at release verification

- evidence records: `2`
- total pass count: `11`
- idempotency passes: `7`
- real-success passes: `4`
- hardware-verified actions: `1`
- framework-verified actions: `1`
- load error: `null`
- write error: `null`

## RC1 packaging smoke tests

The actual Red Queen `1.0.0-rc1` package then passed read-only release smoke tests:

| Gate | Result |
|---|---|
| Startup | PASS |
| `wnhf.release_info` | PASS |
| `wnhf.system_status` | PASS — health 100, warnings 0, errors 0 |
| `wnhf.public_api` | PASS — 66/66 classified, duplicates 0 |
| `wnhf.qualification` | PASS — health 100, persistent evidence intact |

No additional hardware command was required for the branding/package smoke test because execution/provider/feedback/qualification logic was preserved from the already live-verified baseline.

## Reference installation snapshot

At final system-status verification the live house reported:

- house: `Weidnerhome`
- rooms: `22`
- lights: `43`
- enabled lights: `40`
- controllable lights: `38`
- covers: `17`
- openings: `21`
- decisions: `5`
- policies: `5`
- registry valid: yes
- validation quality score: `100`
- system health score: `100`
