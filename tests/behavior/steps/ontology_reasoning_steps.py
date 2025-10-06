# mypy: ignore-errors
import rdflib
from pytest_bdd import given, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.storage import StorageManager, teardown


@scenario(
    "../features/ontology_reasoning.feature",
    "Infer subclass relations through orchestrator",
)
def test_infer_subclass_relations():
    """Infer subclass relations through orchestrator."""
    pass


@given("the storage system is configured for in-memory RDF")
def configure_in_memory_rdf(tmp_path, monkeypatch):
    teardown(remove_db=True)
    cfg = ConfigModel(
        storage=StorageConfig(
            rdf_backend="memory",
            rdf_path=str(tmp_path / "rdf"),
            ontology_reasoner="rdfs",
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    StorageManager.setup()


@given("I have loaded an ontology defining subclasses")
def load_subclass_ontology(tmp_path):
    onto = tmp_path / "onto.ttl"
    onto.write_text(
        """
@prefix ex: <http://example.com/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
ex:A rdfs:subClassOf ex:B .
"""
    )
    StorageManager.load_ontology(str(onto))


@given("I have an instance of the subclass")
def add_subclass_instance():
    store = StorageManager.get_rdf_store()
    store.add(
        (
            rdflib.URIRef("http://example.com/x"),
            rdflib.RDF.type,
            rdflib.URIRef("http://example.com/A"),
        )
    )


@when("I infer relations via the orchestrator")
def infer_via_orchestrator():
    Orchestrator.infer_relations()


@then(
    "querying the ontology for the superclass via the orchestrator should include the instance"
)
def check_query_via_orchestrator():
    res = Orchestrator.query_ontology(
        "ASK { <http://example.com/x> a <http://example.com/B> }"
    )
    assert res.askAnswer
