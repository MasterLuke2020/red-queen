# Red Queen 1.0.0-rc13 Integration Feature Matrix

| Feature | RC13 status |
|---|---|
| Managed configurator | Supported |
| Managed create/edit | Supported for rooms, lights, covers, openings and plants |
| Managed enable/disable | Supported |
| Managed guarded deletion | Supported with explicit confirmation |
| Stable semantic IDs during edit | Required |
| Referenced-room deletion protection | Supported |
| Manual registry | Read-only; never silently adopted |
| Entity/Provider diagnostics | Supported for explicitly configured references |
| Native lights/covers/access/garage/plants | Supported |
| `garage.stop` | Supported when dedicated STOP command is configured |
| Generated dashboard | Supported at `/red-queen` |
| Native unique-ID entity binding | Supported |
| Explicit dashboard create/update | Supported |
| Registry-source freshness detection | Supported |
| Restart persistence | Supported |
| Mandatory custom Lovelace cards | None |
| Direct provider controls from dashboard | Not allowed |
| Arbitrary cover positioning | Not advertised |
| Blade position inference | Not advertised |

Canonical execution API remains `1.0`; canonical real-execution contract remains
`2.3-rc11` because RC13 does not change physical execution semantics.
