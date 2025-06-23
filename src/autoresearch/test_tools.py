"""Testing tools for A2A/MCP interactions.

This module provides functions for testing A2A and MCP interfaces. It allows users
to send test requests to these interfaces and verify the responses.
"""

import json
import requests
from typing import Dict, Any, List, Optional
import time

from .logging_utils import get_logger

logger = get_logger(__name__)


class MCPTestClient:
    """Client for testing MCP interfaces."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        """Initialize the MCP test client.

        Args:
            host: The host where the MCP server is running
            port: The port where the MCP server is running
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the MCP server.

        Returns:
            A dictionary with the test results
        """
        try:
            response = requests.get(f"{self.base_url}/")
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "content": response.text,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def test_research_tool(self, query: str) -> Dict[str, Any]:
        """Test the research tool by sending a query.

        Args:
            query: The query to send

        Returns:
            A dictionary with the test results
        """
        try:
            # Create the request payload
            payload = {"query": query}

            # Send the request
            start_time = time.time()
            response = requests.post(f"{self.base_url}/tools/research", json=payload)
            end_time = time.time()

            # Parse the response
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"error": "Invalid JSON response"}

            # Return the results
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response_json,
                "time_taken": end_time - start_time,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_test_suite(self, queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a test suite on the MCP server.

        Args:
            queries: A list of queries to test. If None, default queries will be used.

        Returns:
            A dictionary with the test results
        """
        if queries is None:
            queries = [
                "What is quantum computing?",
                "Who was Albert Einstein?",
                "What is the capital of France?",
            ]

        # Test connection
        connection_test = self.test_connection()

        # Test research tool
        research_tests = []
        for query in queries:
            research_test = self.test_research_tool(query)
            research_tests.append({"query": query, "result": research_test})

        # Return the results
        return {"connection_test": connection_test, "research_tests": research_tests}


class A2ATestClient:
    """Client for testing A2A interfaces."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        """Initialize the A2A test client.

        Args:
            host: The host where the A2A server is running
            port: The port where the A2A server is running
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the A2A server.

        Returns:
            A dictionary with the test results
        """
        try:
            response = requests.get(f"{self.base_url}/")
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "content": response.text,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def test_query(self, query: str) -> Dict[str, Any]:
        """Test the query endpoint by sending a query.

        Args:
            query: The query to send

        Returns:
            A dictionary with the test results
        """
        try:
            # Create the request payload
            payload = {"type": "query", "content": {"query": query}}

            # Send the request
            start_time = time.time()
            response = requests.post(f"{self.base_url}/message", json=payload)
            end_time = time.time()

            # Parse the response
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"error": "Invalid JSON response"}

            # Return the results
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response_json,
                "time_taken": end_time - start_time,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def test_capabilities(self) -> Dict[str, Any]:
        """Test the capabilities endpoint.

        Returns:
            A dictionary with the test results
        """
        try:
            # Create the request payload
            payload = {"type": "command", "content": {"command": "get_capabilities"}}

            # Send the request
            start_time = time.time()
            response = requests.post(f"{self.base_url}/message", json=payload)
            end_time = time.time()

            # Parse the response
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"error": "Invalid JSON response"}

            # Return the results
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response_json,
                "time_taken": end_time - start_time,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_test_suite(self, queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a test suite on the A2A server.

        Args:
            queries: A list of queries to test. If None, default queries will be used.

        Returns:
            A dictionary with the test results
        """
        if queries is None:
            queries = [
                "What is quantum computing?",
                "Who was Albert Einstein?",
                "What is the capital of France?",
            ]

        # Test connection
        connection_test = self.test_connection()

        # Test capabilities
        capabilities_test = self.test_capabilities()

        # Test queries
        query_tests = []
        for query in queries:
            query_test = self.test_query(query)
            query_tests.append({"query": query, "result": query_test})

        # Return the results
        return {
            "connection_test": connection_test,
            "capabilities_test": capabilities_test,
            "query_tests": query_tests,
        }


def format_test_results(results: Dict[str, Any], format: str = "markdown") -> str:
    """Format test results in the specified format.

    Args:
        results: The test results to format
        format: The format to use (markdown, json, or plain)

    Returns:
        The formatted test results
    """
    if format == "json":
        return json.dumps(results, indent=2)
    elif format == "plain":
        output = []

        # Format connection test
        if "connection_test" in results:
            output.append("Connection Test:")
            output.append(f"  Status: {results['connection_test']['status']}")
            if "error" in results["connection_test"]:
                output.append(f"  Error: {results['connection_test']['error']}")
            elif "status_code" in results["connection_test"]:
                output.append(
                    f"  Status Code: {results['connection_test']['status_code']}"
                )

        # Format capabilities test
        if "capabilities_test" in results:
            output.append("\nCapabilities Test:")
            output.append(f"  Status: {results['capabilities_test']['status']}")
            if "error" in results["capabilities_test"]:
                output.append(f"  Error: {results['capabilities_test']['error']}")
            elif "response" in results["capabilities_test"]:
                output.append(
                    f"  Time Taken: {results['capabilities_test']['time_taken']:.2f} seconds"
                )

        # Format query tests
        if "query_tests" in results:
            output.append("\nQuery Tests:")
            for i, test in enumerate(results["query_tests"]):
                output.append(f"\n  Query {i + 1}: {test['query']}")
                output.append(f"    Status: {test['result']['status']}")
                if "error" in test["result"]:
                    output.append(f"    Error: {test['result']['error']}")
                elif "response" in test["result"]:
                    output.append(
                        f"    Time Taken: {test['result']['time_taken']:.2f} seconds"
                    )

        # Format research tests
        if "research_tests" in results:
            output.append("\nResearch Tests:")
            for i, test in enumerate(results["research_tests"]):
                output.append(f"\n  Query {i + 1}: {test['query']}")
                output.append(f"    Status: {test['result']['status']}")
                if "error" in test["result"]:
                    output.append(f"    Error: {test['result']['error']}")
                elif "response" in test["result"]:
                    output.append(
                        f"    Time Taken: {test['result']['time_taken']:.2f} seconds"
                    )

        return "\n".join(output)
    else:  # markdown
        output = []

        # Format connection test
        if "connection_test" in results:
            output.append("## Connection Test")
            output.append(f"**Status:** {results['connection_test']['status']}")
            if "error" in results["connection_test"]:
                output.append(f"**Error:** {results['connection_test']['error']}")
            elif "status_code" in results["connection_test"]:
                output.append(
                    f"**Status Code:** {results['connection_test']['status_code']}"
                )

        # Format capabilities test
        if "capabilities_test" in results:
            output.append("\n## Capabilities Test")
            output.append(f"**Status:** {results['capabilities_test']['status']}")
            if "error" in results["capabilities_test"]:
                output.append(f"**Error:** {results['capabilities_test']['error']}")
            elif "response" in results["capabilities_test"]:
                output.append(
                    f"**Time Taken:** {results['capabilities_test']['time_taken']:.2f} seconds"
                )

        # Format query tests
        if "query_tests" in results:
            output.append("\n## Query Tests")
            for i, test in enumerate(results["query_tests"]):
                output.append(f"\n### Query {i + 1}: {test['query']}")
                output.append(f"**Status:** {test['result']['status']}")
                if "error" in test["result"]:
                    output.append(f"**Error:** {test['result']['error']}")
                elif "response" in test["result"]:
                    output.append(
                        f"**Time Taken:** {test['result']['time_taken']:.2f} seconds"
                    )

        # Format research tests
        if "research_tests" in results:
            output.append("\n## Research Tests")
            for i, test in enumerate(results["research_tests"]):
                output.append(f"\n### Query {i + 1}: {test['query']}")
                output.append(f"**Status:** {test['result']['status']}")
                if "error" in test["result"]:
                    output.append(f"**Error:** {test['result']['error']}")
                elif "response" in test["result"]:
                    output.append(
                        f"**Time Taken:** {test['result']['time_taken']:.2f} seconds"
                    )

        return "\n".join(output)
