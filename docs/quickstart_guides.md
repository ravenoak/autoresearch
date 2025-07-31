# Autoresearch Quickstart Guides

This document provides quickstart guides for each interface type of the Autoresearch system.

## CLI Quickstart Guide

### Installation

```bash
# Install with uv (recommended)
uv venv
uv pip install -e '.[full,parsers,git,llm,dev]'

# Alternatively, use pip
pip install autoresearch
```

### Basic Usage

1. **Run a simple query:**

```bash
autoresearch search "What is the capital of France?"
```

2. **Specify reasoning mode:**

```bash
autoresearch search "What is the capital of France?" --mode dialectical
```

Available reasoning modes:
- `direct`: Uses only the Synthesizer agent
- `dialectical` (default): Rotates through agents in a thesis→antithesis→synthesis cycle
- `chain-of-thought`: Loops the Synthesizer agent

3. **Specify Primus start index (dialectical mode):**

```bash
autoresearch search "What is the capital of France?" --mode dialectical --primus-start 1
```

4. **Enable ontology reasoning:**

```bash
autoresearch search "What is the capital of France?" --ontology schema.ttl --infer-relations
```

Use `--ontology-reasoner` to specify a custom reasoning engine.

5. **Export results to a file:**

```bash
# Export as JSON
autoresearch search "What is the capital of France?" --output json > result.json

# Export as Markdown
autoresearch search "What is the capital of France?" --output markdown > result.md
```

6. **Visualize query results:**

```bash
autoresearch visualize "What is the capital of France?" graph.png
```

7. **Show an inline graph after searching:**

```bash
autoresearch search "Explain AI ethics" --visualize
```

### Configuration

1. **View current configuration:**

```bash
autoresearch config
```

2. **Update reasoning configuration:**

```bash
autoresearch config reasoning --loops 3
```

3. **Show current reasoning settings:**

```bash
autoresearch config reasoning --show
```

### Monitoring

1. **Show system metrics:**

```bash
autoresearch monitor
```

Use `-w`/`--watch` to refresh continuously.

2. **Start the interactive monitor:**

```bash
autoresearch monitor run
```

Press `Ctrl+C` to exit.

### Shell Completion

1. **Enable shell completion for Bash:**

```bash
autoresearch --install-completion bash
```

2. **Enable shell completion for Zsh:**

```bash
autoresearch --install-completion zsh
```

## Streamlit GUI Quickstart Guide

### Starting the GUI

```bash
autoresearch gui
```

This will start the Streamlit server and open the GUI in your default web browser.

### Basic Usage

1. **Enter a query:**
   - Type your query in the text input field at the top of the page
   - Click the "Run" button or press Enter

2. **View results:**
   - The answer will appear in the "Answer" tab
   - Click on other tabs to view reasoning, citations, and the knowledge graph

3. **Export results:**
   - Click the "Export" button
   - Choose the format (JSON or Markdown)
   - Save the file to your computer

### Configuration

1. **Access configuration:**
   - Click on "Configuration" in the sidebar

2. **Edit configuration:**
   - Modify values in the form
   - Click "Save Changes" to apply

3. **Use configuration presets:**
   - Select a preset from the dropdown
   - Click "Apply Preset"

### History

1. **View query history:**
   - Click on "History" in the sidebar
   - See a list of previous queries

2. **Rerun a query:**
   - Find the query in the history
   - Click the "Rerun" button

## A2A (Agent-to-Agent) Interface Quickstart Guide

### Starting the A2A Server

```bash
autoresearch serve_a2a --host 0.0.0.0 --port 8765
```

### Basic Usage with Python

```python
import asyncio
import httpx
from a2a.client import A2AClient
from a2a.utils.message import new_agent_text_message
from a2a.types import MessageSendParams, SendMessageRequest


async def main() -> None:
    async with httpx.AsyncClient() as http_client:
        client = A2AClient(http_client, url="http://localhost:8765/")
        params = MessageSendParams(message=new_agent_text_message("What is the capital of France?"))
        request = SendMessageRequest(id="1", params=params)
        response = await client.send_message(request)
        print(response.result)

asyncio.run(main())
```

### Basic Usage with cURL

```bash
curl -X POST http://localhost:8765/ \
  -H "Content-Type: application/json" \
  -d '{"type": "query", "message": {"messageId": "1", "role": "agent", "parts": [{"kind": "text", "text": "What is the capital of France?"}]}}'
```

### Discovering Capabilities

```python
import requests

# Get capabilities
response = requests.get("http://localhost:8000/capabilities")
capabilities = response.json()

# Print available capabilities
for capability in capabilities:
    print(f"Capability: {capability['name']}")
    print(f"Description: {capability['description']}")
    print(f"Endpoint: {capability['endpoint']}")
    print()
```

## MCP (Multi-Agent Communication Protocol) Interface Quickstart Guide

### Starting the API Server

```bash
uvicorn autoresearch.api:app --host 0.0.0.0 --port 8000
```

### Basic Usage with Python

```python
import requests
import json
from datetime import datetime

# Define the API endpoint
url = "http://localhost:8000/mcp"

# Prepare the MCP message
headers = {"Content-Type": "application/json"}
message = {
    "type": "query",
    "content": {
        "query": "What is the capital of France?",
        "reasoning_mode": "dialectical"
    },
    "metadata": {
        "sender": "external_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
}

# Send the message
response = requests.post(url, headers=headers, data=json.dumps(message))

# Process the response
if response.status_code == 200:
    result = response.json()
    print(f"Message Type: {result['type']}")
    print(f"Answer: {result['content']['answer']}")
    print(f"Reasoning: {result['content']['reasoning']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Basic Usage with cURL

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "type": "query",
    "content": {
      "query": "What is the capital of France?",
      "reasoning_mode": "dialectical"
    },
    "metadata": {
      "sender": "external_agent",
      "timestamp": "2023-06-01T12:00:00Z"
    }
  }'
```

### MCP Message Types

The MCP interface supports the following message types:

1. **query**: Send a query to the system
2. **response**: Receive a response from the system
3. **error**: Receive an error message
4. **status**: Request or receive system status
5. **capability**: Request or receive capability information

Example of a status request:

```python
status_message = {
    "type": "status",
    "content": {},
    "metadata": {
        "sender": "external_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
}

response = requests.post(url, headers=headers, data=json.dumps(status_message))
status = response.json()
print(f"System Status: {status['content']['status']}")
print(f"Active Agents: {', '.join(status['content']['active_agents'])}")
```

These quickstart guides provide the essential information needed to get started with each interface of the Autoresearch system. For more detailed information, refer to the full documentation.
