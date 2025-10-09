# mypy: ignore-errors
"""Integration tests covering CLI SPARQL utilities."""

from __future__ import annotations

import pytest

from autoresearch.cli_utils import sparql_query_cli


@pytest.mark.integration
def test_sparql_query_cli_handles_missing_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI should tolerate result sets without a ``vars`` attribute."""

    outputs: list[str] = []

    rows: list[tuple[str, str]] = [("subject", "object")]

    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.query_rdf",
        staticmethod(lambda _query: rows),
    )

    def fake_tabulate(
        rows_arg: list[tuple[str, str]],
        headers: list[str] | None = None,
        tablefmt: str = "github",
        **kwargs: object,
    ) -> str:
        return f"{headers}:{rows_arg}"

    monkeypatch.setattr("tabulate.tabulate", fake_tabulate)
    monkeypatch.setattr("autoresearch.cli_utils.console.print", outputs.append)

    sparql_query_cli("SELECT ?s ?o WHERE { ?s ?p ?o }", apply_reasoning=False)

    assert outputs == ["[]:[['subject', 'object']]"]
