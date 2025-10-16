# Logging Subsystem Specification

## Overview

The autoresearch logging subsystem provides unified, structured logging across all interfaces (CLI, API, GUI, MCP) with comprehensive security hardening, performance optimization, and developer experience enhancements. It combines Loguru and structlog for structured JSON logging while maintaining compatibility with the standard library logging module.

## Core Components

### Logging Infrastructure
- **Loguru**: High-level logging library with structured output and async support
- **Structlog**: Structured logging with processors for consistent formatting
- **InterceptHandler**: Bridges standard library logging to Loguru
- **SensitiveDataFilter**: Automatic sanitization of sensitive information
- **CorrelationContext**: Thread-safe correlation ID management

## Log Levels and Semantic Meanings

| Level | Numeric | Purpose | Usage Guidelines |
|-------|---------|---------|------------------|
| `CRITICAL` | 50 | System failure | Application cannot continue; requires immediate attention |
| `ERROR` | 40 | Error conditions | Unexpected failures that prevent normal operation |
| `WARNING` | 30 | Warning conditions | Unexpected conditions that don't prevent operation |
| `INFO` | 20 | Informational | General operational messages; default level |
| `DEBUG` | 10 | Debug information | Detailed diagnostic information for development |

## Structured Logging Format

All logs follow a consistent JSON structure:

```json
{
  "timestamp": "2025-10-07T14:30:45.123456Z",
  "level": "INFO",
  "logger": "autoresearch.search.core",
  "message": "Query processing started",
  "correlation_id": "req-123e4567-e89b-12d3-a456-426614174000",
  "operation": "search_query",
  "user_id": 123,
  "query_length": 42,
  "backend": "duckdb"
}
```

### Required Fields
- `timestamp`: ISO 8601 format in UTC
- `level`: Log level name (CRITICAL, ERROR, WARNING, INFO, DEBUG)
- `logger`: Component/module name
- `message`: Human-readable log message

### Optional Fields
- `correlation_id`: Request correlation identifier
- `operation`: Operation being performed
- `user_id`: User identifier (sanitized)
- `error_code`: Structured error code
- `duration_ms`: Operation duration in milliseconds
- `metadata`: Additional contextual data

## Security Requirements

### Sensitive Data Sanitization

**Automatic Sanitization Patterns:**
- API keys (various formats: `sk_`, `Bearer `, `xoxp-`, etc.)
- Passwords/secrets in field names (`password`, `secret`, `token`, `key`)
- Email addresses (format: `user@domain.com`)
- Credit card numbers (format: `XXXX-XXXX-XXXX-XXXX`)
- Phone numbers (various international formats)
- URLs with embedded credentials (`https://user:pass@host.com`)
- JWT tokens (format: `eyJ...`)
- Database connection strings
- Social Security Numbers (US format: `XXX-XX-XXXX`)

**Sanitization Rules:**
- Replace sensitive values with `[REDACTED]`
- Preserve key names for debugging context
- Handle nested dictionaries and lists recursively
- Support configurable sensitivity levels (strict, normal, permissive)
- Performance target: < 1ms per log entry

### Audit Logging

**Mandatory Audit Events:**
- Authentication attempts (success/failure)
- Authorization failures
- Configuration changes
- API key generation/usage
- Rate limit violations
- Suspicious activity patterns

**Audit Log Format:**
```json
{
  "timestamp": "2025-10-07T14:30:45.123456Z",
  "event_type": "auth_attempt",
  "actor": "user:alice",
  "action": "login",
  "resource": "system",
  "outcome": "success",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "correlation_id": "req-123e4567-e89b-12d3-a456-426614174000"
}
```

**Security Invariants:**
- Audit logs cannot be disabled in production
- Audit logs are tamper-evident (future: cryptographic signatures)
- Audit logs include actor, action, resource, timestamp, outcome
- Audit logs are stored separately from application logs

## Performance Requirements

### Overhead Budget
- **Maximum overhead**: 5% of total application performance
- **p99 latency**: < 10ms per log entry (including sanitization)
- **Memory impact**: < 1MB per 1000 log entries
- **Throughput**: Support 1000+ log entries/second without degradation

### Sampling Strategy
- **Default sampling rate**: 100% (no sampling)
- **High-volume sampling**: Configurable per log level
- **Deterministic sampling**: Hash-based (not random) for consistency
- **Never sample**: CRITICAL and ERROR levels always logged
- **Audit logs**: Never sampled

### Async Logging (Optional)
- **Queue size**: Configurable (default: 10,000 entries)
- **Back-pressure handling**: Block/drop/sample strategies
- **Graceful shutdown**: Flush queue on application exit
- **Thread safety**: Concurrent access without locks

## Multi-Interface Consistency

### Interface Requirements

**CLI Interface:**
- Correlation IDs generated per command execution
- Progress indicators with structured context
- Error messages with actionable suggestions
- Verbose/debug modes with appropriate log levels

**API Interface:**
- Correlation IDs from request headers (`X-Correlation-ID`) or generated
- Request/response logging with timing
- Authentication/authorization events audited
- Rate limiting violations logged

**GUI (Streamlit) Interface:**
- Session-based correlation IDs
- Real-time log viewer integration
- User-friendly error messages
- Performance metrics dashboard integration

**MCP Interface:**
- Request correlation across distributed execution
- Agent execution tracing
- Performance monitoring per agent
- Cross-node correlation propagation

## Configuration Management

### Environment Variables

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
AUTORESEARCH_LOG_LEVEL=INFO

# Log format (json, console, auto)
AUTORESEARCH_LOG_FORMAT=auto

# Enable correlation IDs
AUTORESEARCH_LOG_CORRELATION=true

# Enable log sampling (0.0 to 1.0)
AUTORESEARCH_LOG_SAMPLING_RATE=1.0

# Log file path (optional)
AUTORESEARCH_LOG_FILE=/var/log/autoresearch.log

# Enable log rotation
AUTORESEARCH_LOG_ROTATION=true

# Log retention days
AUTORESEARCH_LOG_RETENTION_DAYS=30

# Audit log path (separate from main logs)
AUTORESEARCH_AUDIT_LOG_FILE=/var/log/autoresearch-audit.log

# Security sensitivity level (strict, normal, permissive)
AUTORESEARCH_LOG_SECURITY_LEVEL=normal

# Suppress diagnostic log messages (show only errors and warnings)
AUTORESEARCH_QUIET_LOGS=false
```

### Runtime Configuration

**Dynamic Log Level Adjustment:**
- Support runtime log level changes via API endpoint
- Changes apply immediately without restart
- Log level changes are audited

**Configuration Validation:**
- All configuration options validated at startup
- Invalid values cause startup failure with clear error messages
- Configuration changes trigger audit events

### Log Format Auto-Detection

**TTY Detection Logic:**
- `auto` format (default): Detects terminal interactivity
- Interactive terminals (TTY): Uses `console` format for human readability
- Non-interactive terminals (pipes, files, automation): Uses `json` format for machine parsing
- Override detection with explicit `--log-format` CLI option

**Console Format Features:**
- Human-readable format: `[LEVEL] component: message`
- Preserves correlation IDs in brackets: `[req-12345]`
- Maintains structured context data for debugging
- No JSON parsing overhead for human operators
- Compatible with terminal colors and formatting

## Error Handling

### Logging Failures
- **Graceful degradation**: Logging failures never crash the application
- **Fallback logging**: Fallback to stderr if primary logging fails
- **Error reporting**: Logging errors reported via separate channel
- **Recovery**: Automatic retry for transient logging failures

### Exception Logging
- **Structured context**: Include operation context in exception logs
- **Stack traces**: Include stack traces for ERROR level and above
- **Error categorization**: Categorize errors (transient, recoverable, critical)
- **Recovery suggestions**: Include actionable recovery suggestions

## Monitoring and Observability

### Runtime Statistics
- **Log volume metrics**: Entries per second, by level
- **Performance metrics**: Average latency per log entry, memory usage
- **Error metrics**: Logging failure rate, sanitization errors
- **Sampling metrics**: Actual vs configured sampling rates

### Health Checks
- **Logging health**: Verify logging system operational
- **Configuration validation**: Check configuration consistency
- **Performance thresholds**: Alert if overhead exceeds budget
- **Audit log integrity**: Verify audit logging functional

## Testing Strategy

### Behavior-Driven Development (BDD)

**Feature Files:**
- `tests/behavior/features/logging_subsystem.feature`
- 15+ scenarios covering security, performance, integration

**Step Definitions:**
- `tests/behavior/steps/logging_steps.py`
- Reusable steps for all logging scenarios

### Unit Testing
- **Coverage target**: > 95% for logging utilities
- **Performance tests**: Benchmark all critical paths
- **Security tests**: Adversarial testing of sanitization
- **Integration tests**: End-to-end across interfaces

### Performance Testing
- **Benchmark suite**: `tests/benchmark/test_logging_performance.py`
- **CI integration**: Performance regression detection
- **Load testing**: High-volume logging scenarios
- **Memory testing**: Long-running stability tests

## Migration Strategy

### Backward Compatibility
- **Existing `configure_logging(level=...)` calls preserved**
- **Gradual migration**: New features opt-in via configuration
- **Deprecation warnings**: Clear migration guidance
- **Feature flags**: Enable new features incrementally

### Breaking Changes (v2.0)
- **Logger acquisition**: Standardize to `get_logger(__name__)`
- **Configuration format**: Use `LoggingConfig` dataclass
- **Streamlit integration**: Unified with main logging pipeline

## Algorithms

### Sensitive Data Detection
1. **Pattern Matching**: Regex-based detection of known sensitive patterns
2. **Field Name Analysis**: Check field names for sensitive keywords
3. **Nested Structure Traversal**: Recursively process dictionaries and lists
4. **Unicode Handling**: Support international formats and encodings
5. **Performance Optimization**: Early exit strategies for large payloads

### Correlation ID Management
1. **Context Variables**: Thread-local storage for correlation IDs
2. **Automatic Generation**: UUID-based generation when missing
3. **Propagation**: Context manager for scoped correlation
4. **Integration Points**: Hook into request/response cycles

### Log Sampling
1. **Hash-Based Sampling**: Deterministic sampling using message hash
2. **Level-Aware Sampling**: Different rates per log level
3. **Always-Log Rules**: Critical levels bypass sampling
4. **Rate Adjustment**: Dynamic rate changes at runtime

## Invariants

### Security Invariants
- Sensitive data never appears in logs (verified by automated tests)
- Audit logs maintain complete event history
- Logging failures never expose sensitive information
- Configuration changes are always audited

### Performance Invariants
- Logging overhead remains within 5% budget
- Memory usage grows linearly with log volume
- No memory leaks in long-running scenarios
- Sampling reduces overhead proportionally

### Consistency Invariants
- All interfaces produce identical log formats
- Correlation IDs propagate across all execution paths
- Log levels maintain consistent semantic meaning
- Configuration changes take effect immediately

## Proof Sketch

**Security Proof:**
Assume an attacker attempts to log sensitive data. The `SensitiveDataFilter` processor intercepts all log entries before output, applying sanitization patterns. The filter handles nested structures recursively and supports configurable sensitivity levels. Comprehensive tests verify 100% pattern coverage with no false negatives.

**Performance Proof:**
Assume high-volume logging scenario (1000+ entries/second). The sampling processor uses hash-based deterministic sampling to reduce volume while preserving statistical properties. Async logging with bounded queues prevents blocking. Benchmarks establish baseline performance and CI gates prevent regressions.

**Consistency Proof:**
Assume multi-interface deployment. Correlation ID context managers ensure IDs propagate through all execution paths. Unified configuration and consistent structlog processors guarantee identical output formats across CLI, API, GUI, and MCP interfaces. Integration tests verify end-to-end consistency.

## Simulation Expectations

**Security Testing:**
- Parameterized tests cover 50+ sensitive data patterns
- Adversarial tests attempt to bypass sanitization
- Performance tests verify < 1ms sanitization overhead
- Integration tests verify audit log completeness

**Performance Testing:**
- Benchmark tests establish baseline overhead (< 5%)
- Load tests verify stability under high volume
- Memory tests confirm no leaks over extended periods
- Sampling tests verify overhead reduction

**Integration Testing:**
- BDD scenarios verify multi-interface consistency
- Correlation ID propagation tests across execution paths
- Configuration change tests verify immediate effect
- Error handling tests verify graceful degradation

## Traceability

### Modules
- [src/autoresearch/logging_utils.py][m1] - Core logging infrastructure
- [src/autoresearch/streamlit_app.py][m2] - GUI logging integration
- [src/autoresearch/api/routing.py][m3] - API logging integration
- [src/autoresearch/main/app.py][m4] - CLI logging integration

### Tests
- ../../tests/behavior/features/logging_subsystem.feature - BDD scenarios
- ../../tests/behavior/steps/logging_steps.py - Step definitions
- ../../tests/unit/logging/test_sensitive_data.py - Security tests
- ../../tests/integration/test_performance.py - Performance tests
- ../../tests/integration/test_streamlit_gui.py - Integration tests
- ../../tests/unit/legacy/test_logging_utils.py - Legacy logging tests
- ../../tests/unit/legacy/test_logging_utils_env.py - Environment logging tests

### Documentation
- [docs/logging_best_practices.md][d1] - Developer guide
- [docs/migration/logging_v2.md][d2] - Migration guide
- [docs/deployment/logging_rollout.md][d3] - Rollout strategy

[m1]: ../../src/autoresearch/logging_utils.py
[m2]: ../../src/autoresearch/streamlit_app.py
[m3]: ../../src/autoresearch/api/routing.py
[m4]: ../../src/autoresearch/main/app.py
[t1]: ../../tests/behavior/features/logging_subsystem.feature
[t2]: ../../tests/behavior/steps/logging_steps.py
[t3]: ../../tests/unit/logging/test_sensitive_data.py
[t4]: ../../tests/integration/test_performance.py
[t5]: ../../tests/integration/test_streamlit_gui.py
[t6]: ../../tests/unit/legacy/test_logging_utils.py
[t7]: ../../tests/unit/legacy/test_logging_utils_env.py
[d1]: ../../docs/logging_best_practices.md
[d2]: ../../docs/migration/logging_v2.md
[d3]: ../../docs/deployment/logging_rollout.md
