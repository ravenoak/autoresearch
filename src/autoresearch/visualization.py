from __future__ import annotations

"""Utilities for generating graphical representations of query results."""

from typing import Any

import networkx as nx
import matplotlib
import matplotlib.pyplot as plt

from .models import QueryResponse

matplotlib.use("Agg")


def save_knowledge_graph(result: QueryResponse, output_path: str) -> None:
    """Save a simple knowledge graph visualization to ``output_path``.

    Parameters
    ----------
    result:
        The query response to visualize.
    output_path:
        Path to the PNG file to create.
    """
    G: nx.DiGraph[Any] = nx.DiGraph()
    main_query = "Query"
    G.add_node(main_query, type="query")
    answer = "Answer"
    G.add_node(answer, type="answer")
    G.add_edge(main_query, answer)

    for i, _ in enumerate(result.citations):
        cid = f"Citation {i + 1}"
        G.add_node(cid, type="citation")
        G.add_edge(answer, cid)

    for i, _ in enumerate(result.reasoning):
        rid = f"Reasoning {i + 1}"
        G.add_node(rid, type="reasoning")
        if i == 0:
            G.add_edge(main_query, rid)
        else:
            G.add_edge(f"Reasoning {i}", rid)
        if i == len(result.reasoning) - 1:
            G.add_edge(rid, answer)

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", font_size=8)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
