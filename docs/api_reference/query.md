# Query API

The Query API exposes versioned Pydantic models for interacting with the
system. `QueryRequestV1`, `QueryResponseV1`, `BatchQueryRequestV1` and
`BatchQueryResponseV1` live in `autoresearch.api.models`. Each payload includes
a `version` field so contracts remain stable as internal implementations
evolve.

## Request Model

::: autoresearch.api.models.QueryRequestV1

Example request to `/query`:

```json
{
  "version": "1",
  "query": "What is machine learning?"
}
```

## Response Model

::: autoresearch.api.models.QueryResponseV1

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

## Batch Request

::: autoresearch.api.models.BatchQueryRequestV1

## Batch Response

::: autoresearch.api.models.BatchQueryResponseV1

The batch endpoint wraps individual responses with pagination metadata:

```json
{
  "version": "1",
  "page": 1,
  "page_size": 2,
  "results": [
    {
      "version": "1",
      "answer": "a",
      "citations": [],
      "reasoning": [],
      "metrics": {}
    },
    {
      "version": "1",
      "answer": "b",
      "citations": [],
      "reasoning": [],
      "metrics": {}
    }
  ]
}
```

## Async Response

::: autoresearch.api.models.AsyncQueryResponseV1

Async queries acknowledge receipt and provide a tracking identifier:

```json
{
  "version": "1",
  "query_id": "123"
}
```

## References

- [API models][m1]

[m1]: ../../src/autoresearch/api/models.py
