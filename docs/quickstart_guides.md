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

8. **Download graph exports directly after a search:**

```bash
autoresearch search "Explain AI ethics" --graphml graph.graphml \
  --graph-json graph.json
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

## PySide6 Desktop Quickstart Guide

### Installation

```bash
# Recommended: use uv with the desktop extra
uv sync --extra desktop

# Alternative: install from PyPI with the desktop dependencies
pip install "autoresearch[desktop]"
```

The desktop extra installs PySide6, Qt WebEngine, and the graph libraries that
power the native UI. Ensure system-level Qt dependencies are present on Linux
before launching the app.

### Starting the desktop app

```bash
autoresearch desktop
```

The command boots the PySide6 main window. Configuration and session data load
from the same directories used by the CLI, so saved profiles are shared.

### Running your first query

1. **Compose the prompt:** Enter your research question in the multiline text
   field inside the **QueryPanel**.
2. **Select a reasoning mode:** Choose the agent strategy from the
   **Reasoning Mode** dropdown. The options mirror `autoresearch search --mode`
   so CLI and desktop sessions stay consistent.
3. **Adjust loop depth:** Tune the **Reasoning Loops** spin box to influence
   how deep the orchestration will iterate.
4. **Run the query:** Click **Run Query** to submit. The status bar reports
   progress while agents work.

> **Tip:** The **QueryPanel** remembers the last configuration that produced a
> result. Use the configuration dock to persist different presets per project.

### Inspecting results

Results stream into the tabbed **ResultsDisplay** in the centre of the window:

- **Answer** renders the Markdown synthesis with inline citations.
- **Citations** lists every source with **Open Source** and **Copy Citation**
  buttons.
- **Knowledge Graph** renders the interactive network view when graph data is
  available.
- **Agent Trace** captures the full reasoning transcript.
- **Metrics** surfaces retrieval, planner, and graph statistics.

> **Tip:** Switch tabs in the **ResultsDisplay** to match your current depth.
> The desktop client only loads heavy knowledge-graph assets when you visit the
> corresponding tab, keeping lightweight reviews responsive.

### Managing docks and exports

Three docks sit around the main canvas:

- **Configuration** (Ctrl+1) exposes the JSON editor for runtime settings.
- **Sessions** (Ctrl+2) lists saved runs and lets you restore previous
  responses.
- **Exports** (Ctrl+3) lights up when structured downloads are ready.

Use **View → Configuration/Sessions/Exports** to toggle each dock. When an
export is available, click the corresponding button inside the **Exports** dock
to save JSON, Markdown, or graph artifacts.

> **Tip:** Dock visibility is global. Collapse panes you do not need, then press
> their shortcuts to summon them when you pivot workflows mid-investigation.

### Legacy Streamlit interface

The Streamlit GUI remains available for short-term compatibility. See the
[legacy appendix](#appendix-a-streamlit-gui-quickstart-legacy) for launch and
navigation details while planning your migration.

## A2A (Agent-to-Agent) Interface Quickstart Guide

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

These quickstart guides provide the essential information needed to get
started with each interface of the Autoresearch system. For more detailed
information, refer to the full documentation.

## Appendix A: Streamlit GUI Quickstart (Legacy)

> **Status:** Maintenance only. Follow the
> [PySide6 Migration and Streamlit Removal Plan](pyside6_migration_plan.md) for
> support timelines and mitigation steps.

### Starting the legacy GUI

```bash
autoresearch gui
```

The command launches the Streamlit server and opens the browser interface.

### Basic usage

1. **Enter a query:** Type your prompt into the textbox at the top of the page
   and click **Run** (or press Enter).
2. **Inspect results:** Use the tabs to flip between the answer, reasoning,
   claim audits, metrics, and the knowledge graph. Depth toggles above the
   results control which sections render.
3. **Export:** Press **Export**, choose JSON or Markdown, and download the file.

### Configuration and history

- **Configuration:** Expand the sidebar, open **Configuration**, update values,
  then click **Save Changes**.
- **History:** Select **History** in the sidebar to re-run stored queries.

> **Tip:** Treat the Streamlit workflow as a fallback for teams that have not
> yet deployed the PySide6 desktop runtime. Plan migrations promptly to benefit
> from the native client improvements documented above.
