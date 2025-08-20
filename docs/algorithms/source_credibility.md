# Source Credibility Heuristics

Autoresearch estimates credibility using heuristic domain authority scores.
Each recognized domain receives a value between 0 and 1 derived from curated
lists of trusted sources. Higher scores indicate more reliable domains and
affect the weight of a document in the final ranking.

## Scoring algorithm

The credibility score :math:`s(d)` for a document with domain :math:`d` is
computed using the following logic:

```text
if d in AUTHORITY:
    return AUTHORITY[d]
for suffix, value in AUTHORITY.items():
    if d.endswith(suffix):
        return value
return 0.5
```

The :code:`AUTHORITY` table maps domains and suffixes such as ``.edu`` or
``.gov`` to scores in the :math:`[0, 1]` interval. Unknown domains default to
``0.5``.

These heuristic scores are already normalized to ``[0, 1]`` and require no
additional scaling before being combined with other ranking metrics.

## Example ranking

Assume three results share the same base relevance score of ``0.7`` and a
``source_credibility_weight`` of ``0.2``. The final score is

```
final = (1 - w) * relevance + w * credibility
```

| URL                                   | Credibility | Final score | Rank |
|---------------------------------------|-------------|-------------|------|
| https://en.wikipedia.org/wiki/Python  | 0.90        | 0.74        | 1    |
| https://dept.example.edu/resource     | 0.80        | 0.72        | 2    |
| https://unknown.xyz/post              | 0.50        | 0.64        | 3    |

## Evaluation results

The final ranking score :math:`s(d)` combines normalized BM25
(:math:`b(d)`), semantic similarity (:math:`m(d)`), and credibility
(:math:`c(d)`):

\[
s(d) = w_{bm25} b(d) + w_{sem} m(d) + w_{cred} c(d)
\]

Running `uv run scripts/simulate_scoring.py --query "python"` on the
sample dataset yields the following ranked scores:

| ID | Final | BM25 | Semantic | Credibility |
|----|-------|------|----------|-------------|
| 3  | 0.96  | 1.00 | 1.00     | 0.80        |
| 1  | 0.90  | 0.90 | 0.89     | 0.90        |
| 2  | 0.12  | 0.00 | 0.00     | 0.60        |

## References

- Moz. "Domain Authority."[^moz]

[^moz]: https://moz.com/learn/seo/domain-authority
