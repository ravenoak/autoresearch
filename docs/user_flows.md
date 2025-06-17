# Autoresearch User Flows

This document describes the typical user flows for all interface modalities of the Autoresearch system.

## CLI Interface User Flows

### Basic Query Flow

1. **Start the CLI**
   ```bash
   autoresearch query "What is the capital of France?"
   ```

2. **View Progress**
   - The CLI displays a progress indicator while the query is being processed
   - Symbolic indicators (✓, ✗, ℹ) provide status information

3. **View Results**
   - The answer is displayed in the terminal
   - Additional information like reasoning and citations is shown in a structured format

4. **Export Results (Optional)**
   ```bash
   autoresearch query "What is the capital of France?" --output json > results.json
   ```

### Configuration Flow

1. **View Current Configuration**
   ```bash
   autoresearch config
   ```

2. **Update Configuration**
   ```bash
   autoresearch config set core.loops 3
   ```

3. **Verify Configuration**
   ```bash
   autoresearch config get core.loops
   ```

### Monitoring Flow

1. **Start the Monitor**
   ```bash
   autoresearch monitor
   ```

2. **View System Metrics**
   - The monitor displays real-time metrics about CPU, memory, and token usage

3. **View Agent Activity**
   - The monitor shows which agents are active and their current status

4. **Exit Monitor**
   - Press Ctrl+C to exit the monitor

## Streamlit GUI User Flows

### Basic Query Flow

1. **Start the GUI**
   ```bash
   autoresearch gui
   ```
   This opens the Streamlit interface in your default web browser.

2. **Enter a Query**
   - Type your query in the text input field
   - Click the "Run" button or press Enter

3. **View Progress**
   - A progress indicator shows the query processing status
   - Real-time updates appear as the query is processed

4. **View Results**
   - The answer appears in the "Answer" tab
   - Switch to other tabs to view reasoning, citations, and the knowledge graph
   - The knowledge graph visualization shows relationships between concepts

5. **Export Results (Optional)**
   - Click the "Export" button to download results in JSON or Markdown format

### Configuration Flow

1. **Navigate to Configuration**
   - Click the "Configuration" section in the sidebar

2. **Edit Configuration**
   - Modify configuration values in the form
   - Form validation ensures valid input

3. **Save Configuration**
   - Click "Save Changes" to update the configuration
   - A success message confirms the changes were saved

4. **Apply Preset (Optional)**
   - Select a preset configuration from the dropdown
   - Click "Apply Preset" to use the selected configuration

### History Flow

1. **View Query History**
   - Click the "History" section in the sidebar
   - See a list of previous queries and their results

2. **Rerun a Query**
   - Click the "Rerun" button next to a historical query
   - The query is executed again with the current configuration

3. **Compare Results (Optional)**
   - Select multiple queries to compare their results side by side

## A2A (Agent-to-Agent) Interface User Flows

### Basic Query Flow

1. **Prepare Request**
   ```python
   import requests
   import json

   url = "http://localhost:8000/query"
   headers = {"Content-Type": "application/json"}
   data = {"query": "What is the capital of France?"}
   ```

2. **Send Request**
   ```python
   response = requests.post(url, headers=headers, data=json.dumps(data))
   ```

3. **Process Response**
   ```python
   result = response.json()
   print(f"Answer: {result['answer']}")
   print(f"Reasoning: {result['reasoning']}")
   print(f"Citations: {', '.join(result['citations'])}")
   ```

### Capability Discovery Flow

1. **Request Capabilities**
   ```python
   url = "http://localhost:8000/capabilities"
   response = requests.get(url)
   capabilities = response.json()
   ```

2. **Use Discovered Capabilities**
   ```python
   for capability in capabilities:
       print(f"Capability: {capability['name']}")
       print(f"Description: {capability['description']}")
       print(f"Endpoint: {capability['endpoint']}")
   ```

## MCP (Multi-Agent Communication Protocol) Interface User Flows

### Basic Query Flow

1. **Prepare MCP Message**
   ```python
   import requests
   import json

   url = "http://localhost:8000/mcp"
   headers = {"Content-Type": "application/json"}
   message = {
       "type": "query",
       "content": {
           "query": "What is the capital of France?",
           "reasoning_mode": "dialectical"
       },
       "metadata": {
           "sender": "external_agent",
           "timestamp": "2023-06-01T12:00:00Z"
       }
   }
   ```

2. **Send MCP Message**
   ```python
   response = requests.post(url, headers=headers, data=json.dumps(message))
   ```

3. **Process MCP Response**
   ```python
   result = response.json()
   print(f"Message Type: {result['type']}")
   print(f"Answer: {result['content']['answer']}")
   print(f"Reasoning: {result['content']['reasoning']}")
   ```

## Cross-Modal Flows

### CLI to GUI Flow

1. **Start with CLI Query**
   ```bash
   autoresearch query "What is the capital of France?"
   ```

2. **Switch to GUI**
   ```bash
   autoresearch gui
   ```

3. **View History in GUI**
   - The query history in the GUI includes the query executed via CLI
   - Click on the query to view its results

4. **Modify and Rerun**
   - Edit the query if needed
   - Click "Rerun" to execute the modified query

### Configuration Synchronization Flow

1. **Update Configuration via CLI**
   ```bash
   autoresearch config set core.loops 3
   ```

2. **Open GUI**
   ```bash
   autoresearch gui
   ```

3. **Verify Configuration in GUI**
   - Navigate to the Configuration section
   - The updated value (loops = 3) is reflected in the GUI

4. **Update Configuration via GUI**
   - Change the value in the GUI
   - Save the changes

5. **Verify in CLI**
   ```bash
   autoresearch config get core.loops
   ```
   - The CLI shows the value updated from the GUI

These user flows provide a comprehensive guide to using the different interfaces of the Autoresearch system, highlighting the consistent behavior and seamless integration between them.