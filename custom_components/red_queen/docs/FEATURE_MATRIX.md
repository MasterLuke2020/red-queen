# Red Queen 1.0.0 Integration Feature Matrix

| Feature | Stable 1.0 scope |
|---|---|
| Managed configurator | Supported |
| Managed maintenance | Supported with transaction protection |
| Stable semantic IDs | Required |
| Manual registry | Read-only until explicitly accepted migration |
| Migration & Repair preview | Supported |
| Manual → managed adoption | Source-SHA guarded + mandatory backup |
| Guided entity repair | Explicit same-domain replacement |
| Guided HA area/floor repair | Explicit selected-area re-link |
| Entity/Provider diagnostics | Supported |
| Native lights/covers/access/garage/plants | Supported |
| `garage.stop` | Guarded canonical execution |
| Generated `/red-queen` dashboard | Supported |
| Restart persistence | LIVE VERIFIED |
| HACS installation/redownload | LIVE VERIFIED |
| Climate/media/larger Plant Care | Deferred beyond 1.0 |

Canonical execution API remains `1.0`; canonical real-execution contract remains
`2.3-rc11`.
