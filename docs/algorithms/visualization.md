# Graph Visualization Pipeline

Autoresearch renders knowledge graphs with NetworkX and a force-directed
layout. The pipeline:

1. build a graph from query results,
2. compute positions with the Fruchterman–Reingold algorithm,
3. draw nodes, edges, and labels with Matplotlib.

The layout minimizes the energy function

\[
E = \sum_{(u,v) \in E} \frac{\|p_u - p_v\|^2}{k}
    + \sum_{u \ne v} \frac{k^2}{\|p_u - p_v\|}
\]

ensuring edges remain straight segments between node positions.

## Complexity

Each iteration computes attractive and repulsive forces for every pair of nodes.
With `n` nodes and `i` iterations, time is

\[
T(n) = O(i n^2), \qquad S(n) = O(n).
\]

## Performance

The script [visualization_performance.py][perf] samples layout times:

| nodes | seconds |
| ----- | ------- |
| 10 | 0.0025 |
| 50 | 0.0163 |
| 100 | 0.0234 |
| 200 | 0.1233 |
| 500 | 4.5152 |

Rendering remains interactive for graphs under 200 nodes on typical hardware.

[perf]: ../../scripts/visualization_performance.py

## References

- Thomas M. J. Fruchterman and Edward M. Reingold. "Graph drawing by
  force-directed placement." *Software: Practice and Experience*, 1991.
  <https://doi.org/10.1002/spe.4380211102>
- NetworkX documentation. <https://networkx.org/>
