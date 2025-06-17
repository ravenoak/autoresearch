# A2A and MCP Integration Guide

This document provides detailed information for developers who want to integrate with the Autoresearch system using the Agent-to-Agent (A2A) or Multi-Agent Communication Protocol (MCP) interfaces.

## Overview

Autoresearch provides two primary integration interfaces for external systems:

1. **Agent-to-Agent (A2A)**: A straightforward REST API for direct query/response interactions
2. **Multi-Agent Communication Protocol (MCP)**: A more sophisticated message-based protocol for complex agent interactions

## A2A Integration

The A2A interface is designed for simple integration scenarios where an external system needs to query Autoresearch and receive responses.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Execute a query and return results |
| `/capabilities` | GET | Get information about available capabilities |
| `/metrics` | GET | Get system performance metrics |
| `/health` | GET | Check system health status |

### Query Endpoint

#### Request Format

```json
{
  "query": "What is the capital of France?",
  "reasoning_mode": "dialectical",
  "loops": 3,
  "max_tokens": 1000,
  "include_metrics": true,
  "include_knowledge_graph": true
}
```

Parameters:
- `query` (string, required): The query to execute
- `reasoning_mode` (string, optional): The reasoning mode to use (`direct`, `dialectical`, or `chain-of-thought`)
- `loops` (integer, optional): Number of reasoning loops to perform
- `max_tokens` (integer, optional): Maximum tokens to generate
- `include_metrics` (boolean, optional): Whether to include performance metrics in the response
- `include_knowledge_graph` (boolean, optional): Whether to include the knowledge graph in the response

#### Response Format

```json
{
  "query": "What is the capital of France?",
  "answer": "Paris is the capital of France.",
  "reasoning": "France is a country in Western Europe. Paris is its capital and largest city.",
  "citations": ["Wikipedia: France", "CIA World Factbook"],
  "confidence": 0.95,
  "knowledge_graph": {
    "nodes": [...],
    "edges": [...]
  },
  "metrics": {
    "tokens_used": 450,
    "processing_time_ms": 2345,
    "agent_calls": 3
  }
}
```

Fields:
- `query`: The original query
- `answer`: The answer to the query
- `reasoning`: The reasoning behind the answer
- `citations`: Sources supporting the answer
- `confidence`: Confidence score (0-1)
- `knowledge_graph`: Knowledge graph generated during reasoning (if requested)
- `metrics`: Performance metrics (if requested)

### Capabilities Endpoint

#### Request

```
GET /capabilities
```

#### Response

```json
[
  {
    "name": "query",
    "description": "Execute a query and return results",
    "endpoint": "/query",
    "method": "POST",
    "parameters": {
      "query": {
        "type": "string",
        "required": true,
        "description": "The query to execute"
      },
      "reasoning_mode": {
        "type": "string",
        "required": false,
        "description": "The reasoning mode to use",
        "options": ["direct", "dialectical", "chain-of-thought"],
        "default": "dialectical"
      },
      ...
    }
  },
  ...
]
```

### Error Handling

Errors are returned with appropriate HTTP status codes and a JSON body:

```json
{
  "error": "Invalid query parameter",
  "detail": "Query cannot be empty",
  "status_code": 400
}
```

### Python Integration Example

```python
import requests
import json

class AutoresearchClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def query(self, query_text, reasoning_mode="dialectical", loops=3):
        """Execute a query and return results."""
        url = f"{self.base_url}/query"
        
        payload = {
            "query": query_text,
            "reasoning_mode": reasoning_mode,
            "loops": loops
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            raise Exception(f"Error {error['status_code']}: {error['error']} - {error['detail']}")
    
    def get_capabilities(self):
        """Get information about available capabilities."""
        url = f"{self.base_url}/capabilities"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            raise Exception(f"Error {error['status_code']}: {error['error']} - {error['detail']}")
    
    def get_metrics(self):
        """Get system performance metrics."""
        url = f"{self.base_url}/metrics"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            raise Exception(f"Error {error['status_code']}: {error['error']} - {error['detail']}")
    
    def check_health(self):
        """Check system health status."""
        url = f"{self.base_url}/health"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            raise Exception(f"Error {error['status_code']}: {error['error']} - {error['detail']}")

# Usage example
client = AutoresearchClient()
result = client.query("What is the capital of France?")
print(f"Answer: {result['answer']}")
```

## MCP Integration

The Multi-Agent Communication Protocol (MCP) is designed for more complex integration scenarios where agents need to communicate with each other in a structured way.

### Protocol Overview

MCP is a message-based protocol where each message has a type, content, and metadata. Messages are exchanged via the `/mcp` endpoint.

### Message Structure

```json
{
  "type": "message_type",
  "content": {
    // Message-specific content
  },
  "metadata": {
    "sender": "agent_id",
    "timestamp": "2023-06-01T12:00:00Z",
    "conversation_id": "conv123",
    "message_id": "msg456",
    "in_reply_to": "msg123"
  }
}
```

Fields:
- `type`: The type of message
- `content`: Message-specific content
- `metadata`: Message metadata
  - `sender`: ID of the sending agent
  - `timestamp`: ISO 8601 timestamp
  - `conversation_id`: ID of the conversation (optional)
  - `message_id`: Unique ID for this message (optional)
  - `in_reply_to`: ID of the message this is replying to (optional)

### Message Types

#### Query Message

```json
{
  "type": "query",
  "content": {
    "query": "What is the capital of France?",
    "reasoning_mode": "dialectical",
    "loops": 3
  },
  "metadata": {
    "sender": "external_agent",
    "timestamp": "2023-06-01T12:00:00Z"
  }
}
```

#### Response Message

```json
{
  "type": "response",
  "content": {
    "query": "What is the capital of France?",
    "answer": "Paris is the capital of France.",
    "reasoning": "France is a country in Western Europe. Paris is its capital and largest city.",
    "citations": ["Wikipedia: France", "CIA World Factbook"],
    "confidence": 0.95
  },
  "metadata": {
    "sender": "autoresearch",
    "timestamp": "2023-06-01T12:00:05Z",
    "in_reply_to": "msg123"
  }
}
```

#### Error Message

```json
{
  "type": "error",
  "content": {
    "error": "Invalid query parameter",
    "detail": "Query cannot be empty",
    "status_code": 400
  },
  "metadata": {
    "sender": "autoresearch",
    "timestamp": "2023-06-01T12:00:01Z",
    "in_reply_to": "msg123"
  }
}
```

#### Status Message

```json
{
  "type": "status",
  "content": {
    "status": "processing",
    "progress": 0.5,
    "active_agents": ["synthesizer", "contrarian"],
    "estimated_completion": "2023-06-01T12:00:10Z"
  },
  "metadata": {
    "sender": "autoresearch",
    "timestamp": "2023-06-01T12:00:02Z",
    "in_reply_to": "msg123"
  }
}
```

#### Capability Message

```json
{
  "type": "capability",
  "content": {
    "capabilities": [
      {
        "name": "query",
        "description": "Execute a query and return results",
        "parameters": {
          "query": {
            "type": "string",
            "required": true,
            "description": "The query to execute"
          },
          ...
        }
      },
      ...
    ]
  },
  "metadata": {
    "sender": "autoresearch",
    "timestamp": "2023-06-01T12:00:00Z"
  }
}
```

### Python Integration Example

```python
import requests
import json
import uuid
from datetime import datetime

class MCPClient:
    def __init__(self, base_url="http://localhost:8000", agent_id="external_agent"):
        self.base_url = base_url
        self.agent_id = agent_id
        self.mcp_endpoint = f"{base_url}/mcp"
        self.headers = {"Content-Type": "application/json"}
        
    def send_message(self, message_type, content, in_reply_to=None, conversation_id=None):
        """Send an MCP message and return the response."""
        message_id = str(uuid.uuid4())
        
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        message = {
            "type": message_type,
            "content": content,
            "metadata": {
                "sender": self.agent_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message_id": message_id,
                "conversation_id": conversation_id
            }
        }
        
        if in_reply_to is not None:
            message["metadata"]["in_reply_to"] = in_reply_to
            
        response = requests.post(self.mcp_endpoint, headers=self.headers, data=json.dumps(message))
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")
    
    def query(self, query_text, reasoning_mode="dialectical", loops=3):
        """Send a query message and return the response."""
        content = {
            "query": query_text,
            "reasoning_mode": reasoning_mode,
            "loops": loops
        }
        
        return self.send_message("query", content)
    
    def get_status(self, in_reply_to=None, conversation_id=None):
        """Send a status request message and return the response."""
        return self.send_message("status", {}, in_reply_to, conversation_id)
    
    def get_capabilities(self):
        """Send a capability request message and return the response."""
        return self.send_message("capability", {})

# Usage example
client = MCPClient()
response = client.query("What is the capital of France?")
print(f"Message Type: {response['type']}")
print(f"Answer: {response['content']['answer']}")
```

## Advanced Integration Patterns

### Streaming Responses

For long-running queries, you can use the streaming API to receive incremental updates:

```python
import requests
import json

def stream_query(query_text, base_url="http://localhost:8000"):
    """Stream a query response."""
    url = f"{base_url}/query/stream"
    
    payload = {
        "query": query_text,
        "reasoning_mode": "dialectical"
    }
    
    headers = {"Content-Type": "application/json"}
    
    with requests.post(url, headers=headers, data=json.dumps(payload), stream=True) as response:
        for line in response.iter_lines():
            if line:
                update = json.loads(line.decode('utf-8'))
                yield update

# Usage example
for update in stream_query("What is the capital of France?"):
    if update["type"] == "progress":
        print(f"Progress: {update['progress'] * 100:.0f}%")
    elif update["type"] == "agent_activity":
        print(f"Agent {update['agent']} is {update['status']}")
    elif update["type"] == "complete":
        print(f"Answer: {update['answer']}")
        break
```

### Conversation Context

To maintain conversation context across multiple queries:

```python
import requests
import json

class ContextualClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id = None
        
    def query(self, query_text, reasoning_mode="dialectical"):
        """Execute a query with conversation context."""
        url = f"{self.base_url}/query"
        
        payload = {
            "query": query_text,
            "reasoning_mode": reasoning_mode
        }
        
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
            
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            if not self.conversation_id and "conversation_id" in result:
                self.conversation_id = result["conversation_id"]
            return result
        else:
            error = response.json()
            raise Exception(f"Error {error['status_code']}: {error['error']} - {error['detail']}")

# Usage example
client = ContextualClient()

# First query establishes context
result1 = client.query("What is the capital of France?")
print(f"Answer 1: {result1['answer']}")

# Second query uses the same context
result2 = client.query("What is its population?")
print(f"Answer 2: {result2['answer']}")
```

### Batch Processing

For processing multiple queries in batch:

```python
import requests
import json

def batch_query(queries, base_url="http://localhost:8000"):
    """Execute multiple queries in batch."""
    url = f"{base_url}/query/batch"
    
    payload = {
        "queries": queries
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()
    else:
        error = response.json()
        raise Exception(f"Error {error['status_code']}: {error['error']} - {error['detail']}")

# Usage example
queries = [
    {"query": "What is the capital of France?"},
    {"query": "What is the capital of Germany?"},
    {"query": "What is the capital of Italy?"}
]

results = batch_query(queries)

for i, result in enumerate(results):
    print(f"Query {i+1}: {result['query']}")
    print(f"Answer {i+1}: {result['answer']}")
    print()
```

## Best Practices

1. **Error Handling**: Always implement proper error handling to catch and process API errors.

2. **Rate Limiting**: Be mindful of rate limits and implement backoff strategies for retries.

3. **Streaming for Long Queries**: Use streaming for long-running queries to provide a better user experience.

4. **Conversation Context**: Maintain conversation context for related queries to improve answer quality.

5. **Batch Processing**: Use batch processing for multiple independent queries to improve throughput.

6. **Security**: Implement proper authentication and authorization for production deployments.

7. **Monitoring**: Monitor API usage and performance to identify issues early.

8. **Versioning**: Be prepared for API changes by checking version information in responses.

By following these guidelines and utilizing the provided integration patterns, you can effectively integrate the Autoresearch system into your applications using either the A2A or MCP interfaces.