# Query API

The Query API provides versioned request and response models for interacting
with the system. Each payload includes a `version` field so contracts remain
stable as internal implementations evolve.

## Request Model

Example request to `/query`:

```json
{
  "version": "1",
  "query": "What is machine learning?"
}
```

## Response Model

A successful response includes reasoning and citations:

```json
{
  "version": "1",
  "answer": "Machine learning studies algorithms that learn from data.",
  "citations": ["https://example.com"],
  "reasoning": ["step 1", "step 2"],
  "metrics": {"cycles_completed": 1}
}
```

## Batch Response

The batch endpoint wraps individual responses with pagination metadata:

```json
{
  "version": "1",
  "page": 1,
  "page_size": 2,
  "results": [
    {"version": "1", "answer": "a", "citations": [], "reasoning": [], "metrics": {}},
    {"version": "1", "answer": "b", "citations": [], "reasoning": [], "metrics": {}}
  ]
}
```

## References

- [API models][m1]

[m1]: ../../src/autoresearch/api/models.py
