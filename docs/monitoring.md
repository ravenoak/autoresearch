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

