# Caching

Autoresearch caches search results and text snippets using a TinyDB database. The cache is part of the storage layer shown in the architecture diagram and helps avoid repeated external lookups.

`src/autoresearch/cache.py` exposes helpers to store and retrieve cached data. `Search.external_lookup` checks this cache before contacting any backend.
