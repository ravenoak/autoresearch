# Models

Autoresearch defines Pydantic data models for requests and responses.

- Validation: fields are type checked and required values enforced.
- Hot reload: model definitions support dynamic updates during config reload.
- Schema guarantees: exportable JSON schema documents the public interface.

See also: [../specs/models.md](../specs/models.md).

## Simulation

Automated tests confirm models behavior.

- [Spec](../specs/models.md)
- [Tests](../../tests/integration/test_simple_orchestration.py)
