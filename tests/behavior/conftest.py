import os
import pytest


@pytest.fixture(autouse=True)
def enable_real_vss(monkeypatch):
    """Allow real VSS extension loading in behavior tests."""
    monkeypatch.setenv("REAL_VSS_TEST", "1")
    yield
    monkeypatch.delenv("REAL_VSS_TEST", raising=False)


@pytest.fixture(autouse=True)
def bdd_storage_manager(storage_manager):
    """Use the global temporary storage fixture for behavior tests."""
    yield storage_manager


@pytest.fixture
def storage_error_handler():
    """Fixture for handling storage errors in BDD tests.

    This fixture provides methods for attempting operations that might raise
    storage errors and for verifying the error messages.

    Returns:
        A handler object with methods for working with storage errors.
    """

    class StorageErrorHandler:
        def attempt_operation(
            self, operation, bdd_context, context_key="storage_error"
        ):
            """Attempt an operation that might raise an exception.

            Args:
                operation (callable): The operation to attempt
                bdd_context (dict): The BDD context dictionary
                context_key (str): The key to use for storing the error in the context

            Returns:
                The result of the operation if successful, None otherwise
            """
            from autoresearch.errors import StorageError

            try:
                result = operation()
                bdd_context[context_key] = None
                return result
            except StorageError as e:
                # Catch StorageError specifically to store it in the context
                bdd_context[context_key] = e
                return None
            except Exception as e:
                # Catch any other exception, convert it to a StorageError, and store it
                storage_error = StorageError(
                    f"Unexpected error: {str(e)}",
                    cause=e,
                    suggestion="This is likely a bug in the test or the storage system",
                )
                bdd_context[context_key] = storage_error
                return None

        def verify_error(
            self, bdd_context, expected_message=None, context_key="storage_error"
        ):
            """Verify that a StorageError was raised with the expected message.

            Args:
                bdd_context (dict): The BDD context dictionary
                expected_message (str): The expected error message (substring)
                context_key (str): The key used for storing the error in the context

            Raises:
                AssertionError: If no error was raised or the message doesn't match
            """
            storage_error = bdd_context.get(context_key)
            assert storage_error is not None, "No exception was raised"

            if expected_message:
                error_message = str(storage_error).lower()
                assert expected_message.lower() in error_message, (
                    f"Error message '{error_message}' does not contain '{expected_message}'"
                )

    return StorageErrorHandler()


@pytest.fixture
def claim_factory():
    """Factory fixture for creating claims with different properties.

    This fixture provides a standardized way to create claims for testing,
    with methods for creating valid claims, invalid claims, and claims with
    specific properties.

    Returns:
        A factory object with methods for creating different types of claims.
    """

    class ClaimFactory:
        def create_valid_claim(
            self,
            claim_id="test-claim-123",
            claim_type="fact",
            content="This is a test claim",
            confidence=0.9,
            attributes=None,
            relations=None,
            embedding=None,
        ):
            """Create a valid claim with the specified properties.

            Args:
                claim_id (str): The ID of the claim
                claim_type (str): The type of the claim
                content (str): The content of the claim
                confidence (float): The confidence score of the claim
                attributes (dict): Additional attributes for the claim
                relations (list): Relations to other claims or sources
                embedding (list): Vector embedding for the claim

            Returns:
                dict: A valid claim with the specified properties
            """
            if attributes is None:
                attributes = {"verified": True}

            if relations is None:
                relations = [
                    {
                        "src": claim_id,
                        "dst": "source-1",
                        "rel": "cites",
                        "weight": 1.0,
                    }
                ]

            if embedding is None:
                embedding = [0.1, 0.2, 0.3, 0.4]

            claim = {
                "id": claim_id,
                "type": claim_type,
                "content": content,
                "confidence": confidence,
                "attributes": attributes,
                "relations": relations,
                "embedding": embedding,
            }
            return claim

        def create_invalid_claim(self, missing_field="id"):
            """Create an invalid claim with a missing required field.

            Args:
                missing_field (str): The required field to omit

            Returns:
                dict: An invalid claim with the specified field missing
            """
            claim = self.create_valid_claim()
            del claim[missing_field]
            return claim

        def create_claims_batch(self, count=5):
            """Create a batch of valid claims with different properties.

            Args:
                count (int): The number of claims to create

            Returns:
                list: A list of valid claims
            """
            claims = []
            for i in range(count):
                claim = self.create_valid_claim(
                    claim_id=f"test-claim-{i}",
                    content=f"This is test claim {i}",
                    embedding=[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i],
                )
                claims.append(claim)
            return claims

        def verify_in_networkx(self, claim):
            """Verify that a claim exists in the NetworkX graph.

            Args:
                claim (dict): The claim to verify

            Returns:
                bool: True if the claim exists in the graph, False otherwise
            """
            from autoresearch.storage import StorageManager

            graph = StorageManager.get_graph()
            return (
                claim["id"] in graph.nodes
                and graph.nodes[claim["id"]].get("verified") is True
            )

        def verify_in_duckdb(self, claim):
            """Verify that a claim exists in the DuckDB database.

            Args:
                claim (dict): The claim to verify

            Returns:
                bool: True if the claim exists in the database, False otherwise
            """
            from autoresearch.storage import StorageManager

            conn = StorageManager.get_duckdb_conn()
            result = conn.execute(
                f"SELECT * FROM nodes WHERE id = '{claim['id']}'"
            ).fetchall()
            return len(result) == 1 and result[0][0] == claim["id"]

        def verify_in_rdf(self, claim):
            """Verify that a claim exists in the RDF store.

            Args:
                claim (dict): The claim to verify

            Returns:
                bool: True if the claim exists in the RDF store, False otherwise
            """
            from autoresearch.storage import StorageManager
            import rdflib

            store = StorageManager.get_rdf_store()

            # Check if the claim exists using the triples method instead of SPARQL
            subj = rdflib.URIRef(f"urn:claim:{claim['id']}")
            results = list(store.triples((subj, None, None)))
            return len(results) > 0

    return ClaimFactory()
