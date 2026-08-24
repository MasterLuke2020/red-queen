# Red Queen 1.0.0-rc12 Integration Feature Matrix

| Feature | RC12 status |
|---|---|
| Managed configurator | Supported and retained from RC11 |
| Manual registry | Read-only semantic configuration; dashboard supported |
| Native lights/covers/access/garage/plants | Supported |
| `garage.stop` | Supported when dedicated STOP command is configured |
| Generated dashboard | Supported at `/red-queen` |
| Dashboard overview | Supported |
| Floor views | Supported |
| Room subviews | Supported |
| Plant Care view | Supported |
| System/Diagnostics view | Supported |
| Native unique-ID entity binding | Supported |
| Explicit dashboard create/update | Supported |
| Digest-based update detection | Supported |
| Restart persistence | Supported |
| Mandatory custom Lovelace cards | None |
| Direct provider controls from dashboard | Not allowed |
| Arbitrary cover positioning | Not advertised |
| Blade position inference | Not advertised |

Canonical execution API remains `1.0`; the canonical real-execution contract remains
`2.3-rc11` because RC12 does not change physical execution semantics.
