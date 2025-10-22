from __future__ import annotations

from textwrap import dedent

import httpx

from autoresearch.resources.scholarly.fetchers import ArxivFetcher


def _build_feed(entry: str) -> str:
    return dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
        {entry}
        </feed>
        """
    ).strip()


def test_arxiv_search_parses_metadata(httpx_mock) -> None:
    entry = dedent(
        """\
        <entry>
          <id>http://arxiv.org/abs/2401.01234v1</id>
          <title>Example Paper</title>
          <summary>This is an abstract.</summary>
          <published>2024-01-01T00:00:00Z</published>
          <author><name>A. Researcher</name></author>
          <link href="http://arxiv.org/abs/2401.01234v1" rel="alternate"/>
          <link href="http://arxiv.org/pdf/2401.01234v1" rel="related" type="application/pdf"/>
          <arxiv:doi>10.1234/example</arxiv:doi>
        </entry>
        """
    )
    def _callback(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_build_feed(entry))

    expected_url = str(
        httpx.URL(
            "https://export.arxiv.org/api/query",
            params={"search_query": "all:example", "max_results": "1", "start": "0"},
        )
    )
    httpx_mock.add_callback(
        _callback,
        url=expected_url,
    )
    fetcher = ArxivFetcher()
    results = fetcher.search("example", limit=1)
    assert len(results) == 1
    metadata = results[0]
    assert metadata.title == "Example Paper"
    assert metadata.abstract == "This is an abstract."
    assert metadata.arxiv_id == "2401.01234v1"
    assert metadata.doi == "10.1234/example"
    assert metadata.authors == ("A. Researcher",)


def test_arxiv_fetch_returns_document(httpx_mock) -> None:
    entry = dedent(
        """\
        <entry>
          <id>http://arxiv.org/abs/2401.09999v2</id>
          <title>Another Paper</title>
          <summary>More details here.</summary>
          <published>2024-02-02T12:00:00Z</published>
          <author><name>B. Analyst</name></author>
          <link href="http://arxiv.org/abs/2401.09999v2" rel="alternate"/>
          <link href="http://arxiv.org/pdf/2401.09999v2" rel="related" type="application/pdf"/>
        </entry>
        """
    )
    httpx_mock.add_callback(
        lambda request: httpx.Response(200, text=_build_feed(entry)),
        url=str(
            httpx.URL(
                "https://export.arxiv.org/api/query",
                params={"id_list": "2401.09999v2"},
            )
        ),
    )
    fetcher = ArxivFetcher()
    document = fetcher.fetch("2401.09999v2")
    assert document.metadata.title == "Another Paper"
    assert document.body == "More details here."
    assert "http://arxiv.org/pdf/2401.09999v2" in document.references
