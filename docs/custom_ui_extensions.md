# Custom UI Extensions

This document provides information for developers who want to create custom user interfaces for the Autoresearch system.

## Extension Points Overview

Autoresearch is designed with a modular architecture that allows for custom UI extensions. The system provides several extension points:

1. **Core API**: The foundation for all interfaces, exposing the core functionality
2. **Output Formatting**: Customizable output formatting for different UI needs
3. **Configuration System**: Extensible configuration handling
4. **Event System**: Pub/sub mechanism for real-time updates

## Core API

The Core API is the primary extension point for custom UIs. It provides access to all the functionality of the Autoresearch system.

### Key Components

```python
from autoresearch.core import AutoresearchCore

# Initialize the core
core = AutoresearchCore()

# Execute a query
result = core.query(
    query="What is the capital of France?",
    reasoning_mode="dialectical",
    loops=3
)

# Access configuration
config = core.get_config()

# Update configuration
core.update_config({"core": {"loops": 5}})

# Get system status
status = core.get_status()
```

### Query Response Structure

The query response object has the following structure:

```python
class QueryResponse:
    query: str                # The original query
    answer: str               # The answer to the query
    reasoning: str            # The reasoning behind the answer
    citations: List[str]      # Citations supporting the answer
    confidence: float         # Confidence score (0-1)
    knowledge_graph: Graph    # Knowledge graph generated during reasoning
    metrics: Dict[str, Any]   # Performance metrics
```

## Output Formatting

The output formatting system allows for customizing how results are presented in your UI.

### Customizing Output Format

```python
from autoresearch.output_format import OutputFormat, OutputFormatConfig

# Create a custom output format configuration
config = OutputFormatConfig(
    use_color=True,
    screen_reader_mode=False,
    date_format="%Y-%m-%d %H:%M:%S",
    table_format="grid"
)

# Create an output formatter
formatter = OutputFormat(config)

# Format different types of output
error_message = formatter.format_error("Something went wrong")
success_message = formatter.format_success("Operation completed")
info_message = formatter.format_info("Processing query")
table = formatter.format_table(data, headers=["Name", "Value"])
```

### Creating a Custom Formatter

You can create a custom formatter by subclassing the `OutputFormat` class:

```python
from autoresearch.output_format import OutputFormat

class MyCustomFormatter(OutputFormat):
    def format_error(self, message: str) -> str:
        # Custom error formatting
        return f"ERROR: {message}"
    
    def format_success(self, message: str) -> str:
        # Custom success formatting
        return f"SUCCESS: {message}"
    
    def format_info(self, message: str) -> str:
        # Custom info formatting
        return f"INFO: {message}"
    
    def format_table(self, data: List[List[Any]], headers: List[str] = None) -> str:
        # Custom table formatting
        # ...
        return formatted_table
```

## Configuration System

The configuration system allows for extending the configuration options for your custom UI.

### Adding Custom Configuration Sections

```python
from autoresearch.config import ConfigLoader

# Get the config loader
config_loader = ConfigLoader()

# Register a custom configuration section
config_loader.register_section(
    section="my_custom_ui",
    schema={
        "theme": {"type": "string", "default": "light"},
        "refresh_rate": {"type": "integer", "default": 5},
        "features": {"type": "list", "default": ["feature1", "feature2"]}
    }
)

# Access custom configuration
my_ui_config = config_loader.get_config().get("my_custom_ui", {})
theme = my_ui_config.get("theme", "light")
```

### Configuration Hot-Reload

The configuration system supports hot-reloading, which allows your UI to react to configuration changes:

```python
from autoresearch.config import ConfigLoader

def config_changed_callback(new_config):
    # Update your UI based on the new configuration
    print(f"Configuration changed: {new_config}")

# Register for configuration change notifications
config_loader = ConfigLoader()
config_loader.add_change_listener(config_changed_callback)
```

## Event System

The event system provides a pub/sub mechanism for real-time updates, which is useful for creating reactive UIs.

### Subscribing to Events

```python
from autoresearch.events import EventBus

# Get the event bus
event_bus = EventBus()

# Subscribe to query start events
def on_query_start(query_data):
    print(f"Query started: {query_data['query']}")

event_bus.subscribe("query_start", on_query_start)

# Subscribe to query complete events
def on_query_complete(result_data):
    print(f"Query completed: {result_data['answer']}")

event_bus.subscribe("query_complete", on_query_complete)

# Subscribe to agent activity events
def on_agent_activity(agent_data):
    print(f"Agent {agent_data['name']} is {agent_data['status']}")

event_bus.subscribe("agent_activity", on_agent_activity)
```

### Publishing Events

If your UI needs to publish events:

```python
from autoresearch.events import EventBus

# Get the event bus
event_bus = EventBus()

# Publish a custom event
event_bus.publish("my_custom_event", {
    "source": "my_custom_ui",
    "action": "button_click",
    "details": {"button_id": "run_query"}
})
```

## Creating a Web-Based UI

For web-based UIs, you can use the existing FastAPI server as a foundation:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from autoresearch.api import app as api_app

# Create your UI app
ui_app = FastAPI()

# Mount the API
ui_app.mount("/api", api_app)

# Mount static files
ui_app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Define routes
@ui_app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Run with uvicorn
# uvicorn my_custom_ui:ui_app --reload
```

## Creating a Desktop UI

For desktop UIs, you can use the Core API directly:

```python
import tkinter as tk
from tkinter import ttk
from autoresearch.core import AutoresearchCore

class AutoresearchDesktopUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Autoresearch Desktop")
        
        self.core = AutoresearchCore()
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Create query input
        self.query_frame = ttk.Frame(self.root, padding="10")
        self.query_frame.pack(fill=tk.X)
        
        ttk.Label(self.query_frame, text="Query:").pack(side=tk.LEFT)
        self.query_entry = ttk.Entry(self.query_frame, width=50)
        self.query_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.query_frame, text="Run", command=self.run_query).pack(side=tk.LEFT)
        
        # Create results display
        self.results_frame = ttk.Frame(self.root, padding="10")
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
    def run_query(self):
        query = self.query_entry.get()
        if not query:
            return
            
        # Show loading indicator
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Processing query...")
        self.root.update_idletasks()
        
        # Execute query
        try:
            result = self.core.query(query=query)
            
            # Display results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Answer: {result.answer}\n\n")
            self.results_text.insert(tk.END, f"Reasoning: {result.reasoning}\n\n")
            self.results_text.insert(tk.END, f"Citations: {', '.join(result.citations)}")
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Error: {str(e)}")

# Usage
if __name__ == "__main__":
    root = tk.Tk()
    app = AutoresearchDesktopUI(root)
    root.mainloop()
```

## Best Practices for Custom UIs

1. **Use the Core API**: Always interact with the system through the Core API rather than directly accessing internal components.

2. **Handle Asynchronous Operations**: Many operations in Autoresearch are asynchronous. Ensure your UI can handle this properly.

3. **Implement Proper Error Handling**: Catch and display errors in a user-friendly way.

4. **Support Accessibility**: Ensure your UI is accessible to users with disabilities.

5. **Maintain Consistency**: Follow the same terminology and interaction patterns as the official interfaces.

6. **Test Cross-Modal Integration**: If users might switch between your UI and other interfaces, test that the experience is seamless.

7. **Document Your Extensions**: Provide clear documentation for your custom UI, including installation and usage instructions.

By following these guidelines and utilizing the provided extension points, you can create custom UIs that integrate seamlessly with the Autoresearch system while providing unique value to your users.