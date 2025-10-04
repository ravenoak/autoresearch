# Monitoring

Autoresearch records runtime statistics and exposes them through a
Prometheus endpoint. Clients with the `metrics` permission receive a
`200` response from `/metrics` containing the current counters and gauges.

- Grant the `metrics` permission via `api.role_permissions`.
- When authentication is enabled, missing or invalid credentials return `401`
  with `WWW-Authenticate` headers.
- The `monitor` CLI provides a real time view using `autoresearch monitor
  metrics`.

Additional details on the monitor utilities are available in
[monitor.md](monitor.md).

## Telemetry surface

The :mod:`autoresearch.monitor.telemetry` module exposes helpers for
capturing audit telemetry in a consistent schema. Use
``normalize_audit_payload`` to coerce raw claim audits into the canonical
``AUDIT_TELEMETRY_FIELDS`` set and ``build_audit_telemetry`` to aggregate
status counters, claim identifiers, and instability flags for dashboard
consumers. The helpers accept plain mappings, normalise optional values,
and always emit serialisable dictionaries so monitoring agents can record
the output without additional checks.

