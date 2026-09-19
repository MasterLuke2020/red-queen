# Red Queen 1.0.0-rc14 Integration Feature Matrix

| Feature | RC14 status |
|---|---|
| Managed configurator | Supported |
| Managed create/edit | Supported for rooms, lights, covers, openings and plants |
| Managed enable/disable | Supported |
| Managed guarded deletion | Supported with explicit confirmation |
| Stable semantic IDs during edit/repair | Required |
| Referenced-room deletion protection | Supported |
| Manual registry | Read-only until explicitly accepted migration |
| Migration & Repair preview | Read-only, source-SHA fingerprinted |
| Manual → managed adoption | Explicit prepare + second confirmation + mandatory backup |
| Guided entity-reference repair | Missing/disabled refs; explicit same-domain replacement |
| Guided HA area/floor-link repair | Explicit selected-area re-link |
| Repair stale-write guard | Preview source SHA required |
| Entity/Provider diagnostics | Explicit configured references only |
| Native lights/covers/access/garage/plants | Supported |
| `garage.stop` | Supported when dedicated STOP command is configured |
| Generated dashboard | Supported at `/red-queen` |
| Native unique-ID entity binding | Supported |
| Explicit dashboard create/update | Supported |
| Registry-source freshness detection | Supported |
| Restart persistence | Supported |
| Automatic ambiguous repair | Not allowed |
| Mandatory custom Lovelace cards | None |

Canonical execution API remains `1.0`; canonical real-execution contract remains
`2.3-rc11` because RC14 changes configuration migration/repair behavior, not physical
execution semantics.
