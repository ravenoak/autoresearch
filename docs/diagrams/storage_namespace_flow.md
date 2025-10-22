# Storage Namespace Flow

The diagram highlights how scoped namespace tokens propagate from CLI inputs and
workspace context into the search cache and scholarly storage layers, including
the new multi-format scholarly cache pipeline.

```mermaid
flowchart TD
    cli["CLI --namespace tokens"] --> cfg["search.cache_namespace"]
    workspace["Workspace hints"] --> searchInit["Search initialisation"]
    cfg --> searchInit
    searchInit --> resolver["StorageManager._resolve_namespace_label"]
    resolver --> cacheView["Namespaced search cache"]
    resolver --> scholarly["Scholarly cache persistence"]
    cacheView --> reuse["Consistent cache slots"]
    scholarly --> variants["Content variants (PDF/HTML/Markdown)"]
    scholarly --> provenance["Provenance (version + latency)"]
    variants --> storage["DuckDB / RDF namespaces"]
    provenance --> storage
    storage --> manifests["Workspace manifests auto-attach cached papers"]
```
