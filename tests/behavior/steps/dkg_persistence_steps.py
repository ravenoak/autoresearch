# flake8: noqa
from pytest_bdd import scenario, given, when, then


@given("I have a valid claim with source metadata", target_fixture="valid_claim")
def valid_claim(tmp_path):
    claim = {
        "id": "test-claim-123",
        "type": "fact",
        "content": "This is a test claim",
        "confidence": 0.9,
        "attributes": {"verified": True},
        "relations": [
            {
                "src": "test-claim-123",
                "dst": "source-1",
                "rel": "cites",
                "weight": 1.0,
            }
        ],
        "embedding": [0.1, 0.2, 0.3, 0.4],
    }
    return claim


@when("an agent asserts a new claim")
def agent_asserts_claim(valid_claim):
    from autoresearch.storage import StorageManager

    StorageManager.persist_claim(valid_claim)
    return valid_claim


@then("the claim node should be added to the NetworkX graph in RAM")
def check_networkx_graph(valid_claim):
    from autoresearch.storage import StorageManager

    graph = StorageManager.get_graph()
    assert valid_claim["id"] in graph.nodes
    assert graph.nodes[valid_claim["id"]]["verified"] is True


@when("an agent commits a new claim")
def agent_commits_claim(valid_claim):
    from autoresearch.storage import StorageManager

    StorageManager.persist_claim(valid_claim)
    return valid_claim


@then("a row should be inserted into the `nodes` table")
def check_duckdb_nodes(valid_claim):
    from autoresearch.storage import StorageManager

    conn = StorageManager.get_duckdb_conn()
    result = conn.execute(
        f"SELECT * FROM nodes WHERE id = '{valid_claim['id']}'"
    ).fetchall()
    assert len(result) == 1
    assert result[0][0] == valid_claim["id"]
    assert result[0][1] == valid_claim["type"]
    assert result[0][2] == valid_claim["content"]
    assert result[0][3] == valid_claim["confidence"]


@then("the corresponding `edges` table should reflect relationships")
def check_duckdb_edges(valid_claim):
    from autoresearch.storage import StorageManager

    conn = StorageManager.get_duckdb_conn()
    result = conn.execute(
        f"SELECT * FROM edges WHERE src = '{valid_claim['id']}'"
    ).fetchall()
    assert len(result) == len(valid_claim["relations"])
    assert result[0][0] == valid_claim["relations"][0]["src"]
    assert result[0][1] == valid_claim["relations"][0]["dst"]
    assert result[0][2] == valid_claim["relations"][0]["rel"]
    assert result[0][3] == valid_claim["relations"][0]["weight"]


@then("the embedding should be stored in the `embeddings` vector column")
def check_duckdb_embeddings(valid_claim):
    from autoresearch.storage import StorageManager

    conn = StorageManager.get_duckdb_conn()
    result = conn.execute(
        f"SELECT * FROM embeddings WHERE node_id = '{valid_claim['id']}'"
    ).fetchall()
    assert len(result) == 1
    assert result[0][0] == valid_claim["id"]
    assert result[0][1] == valid_claim["embedding"]


@when("the system writes provenance data")
def system_writes_provenance(valid_claim):
    from autoresearch.storage import StorageManager

    StorageManager.persist_claim(valid_claim)
    return valid_claim


@then("a new quad should appear in the RDFlib store")
def check_rdflib_store(valid_claim):
    from autoresearch.storage import StorageManager
    import rdflib

    store = StorageManager.get_rdf_store()
    subj = rdflib.URIRef(f"urn:claim:{valid_claim['id']}")
    results = list(store.triples((subj, None, None)))
    assert len(results) > 0


@then("queries should return the quad via SPARQL")
def check_sparql_query(valid_claim):
    from autoresearch.storage import StorageManager
    import rdflib

    store = StorageManager.get_rdf_store()
    query = f"""
    SELECT ?p ?o
    WHERE {{
        <urn:claim:{valid_claim['id']}> ?p ?o .
    }}
    """
    results = list(store.query(query))
    assert len(results) > 0


@scenario("../features/dkg_persistence.feature", "Persist claim in RAM")
def test_persist_ram():
    pass


@scenario("../features/dkg_persistence.feature", "Persist claim in DuckDB")
def test_persist_duckdb():
    pass


@scenario("../features/dkg_persistence.feature", "Persist claim in RDF quad-store")
def test_persist_rdf():
    pass
