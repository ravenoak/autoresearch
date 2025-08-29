# Models

The models module defines Pydantic schemas used throughout
Autoresearch. These models validate data, allow hot reload to plug in
updated configuration, and guarantee stable schemas for
serialization.

## Validation

Each model validates input on creation, rejecting incompatible types
and missing fields. This guards every layer from malformed data.

## Hot Reload

When configuration hot reload occurs, new values are parsed into the
same models, ensuring any updated settings respect the original schema.

## Schema Guarantees

The models expose explicit fields for answers, citations, reasoning,
and metrics. These definitions allow reliable serialization and
inspection across the system.
