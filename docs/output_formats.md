# Autoresearch Output Formats

This document describes the available output formats in Autoresearch and their use cases.

## Available Formats

Autoresearch supports the following output formats:

1. **Markdown** (default): Rich text format with headings and lists
2. **JSON**: Structured format for programmatic consumption
3. **Plain Text**: Simple text format for basic terminal output
4. **Custom Templates**: User-defined templates for specialized output formats

## Format Details and Use Cases

### Markdown

Markdown is the default output format when running Autoresearch in an interactive terminal. It provides a rich, human-readable format with headings, lists, and other formatting.

**Structure:**
```markdown
# Answer
The answer to the query...

## Citations
- Citation 1
- Citation 2
- ...

## Reasoning
- Reasoning step 1
- Reasoning step 2
- ...

## Metrics
- **metric_name**: value
- ...
```

**Use Cases:**
- Interactive terminal usage
- Saving results to a file for later reference
- Including results in documentation or reports

**Example:**
```bash
autoresearch search "What is quantum computing?" --output markdown
```

### JSON

JSON format provides a structured representation of the query results that can be easily parsed by other programs. This is the default format when the output is piped to another program.

**Structure:**
```json
{
  "answer": "The answer to the query...",
  "citations": [
    {"text": "Citation 1", "source": "Source 1", "relevance": 0.95},
    {"text": "Citation 2", "source": "Source 2", "relevance": 0.85}
  ],
  "reasoning": [
    "Reasoning step 1",
    "Reasoning step 2"
  ],
  "metrics": {
    "metric_name": "value"
  }
}
```

**Use Cases:**
- Integration with other tools or scripts
- Storing results in a database
- Post-processing results with other programs

**Example:**
```bash
autoresearch search "What is quantum computing?" --output json > results.json
```

### Plain Text

Plain text format provides a simple, unformatted representation of the query results. This is useful for environments where formatting is not supported or needed.

**Structure:**
```
Answer:
The answer to the query...

Citations:
Citation 1
Citation 2
...

Reasoning:
Reasoning step 1
Reasoning step 2
...

Metrics:
metric_name: value
...
```

**Use Cases:**
- Environments without support for rich formatting
- Simple logging or output capture
- Maximum compatibility with other tools

**Example:**
```bash
autoresearch search "What is quantum computing?" --output plain
```

### Custom Templates

Custom templates allow you to define your own output format using the string.Template syntax. This is useful for specialized output formats or integration with specific tools.

**Creating a Custom Template:**

1. Create a template file with the `.tpl` extension
2. Place it in one of the following locations:
   - Current directory: `./templates/`
   - User config directory: `~/.config/autoresearch/templates/`
   - System-wide config directory: `/etc/autoresearch/templates/`

**Template Variables:**
- `${answer}`: The answer to the query
- `${citations}`: The citations as a formatted string
- `${reasoning}`: The reasoning steps as a formatted string
- `${metrics}`: The metrics as a formatted string
- `${metric_name}`: Individual metrics by name

**Example Template (HTML):**
```html
<!-- templates/html.tpl -->
<html>
<head><title>Autoresearch Results</title></head>
<body>
  <h1>Answer</h1>
  <p>${answer}</p>
  
  <h2>Citations</h2>
  <ul>
    ${citations}
  </ul>
  
  <h2>Reasoning</h2>
  <ol>
    ${reasoning}
  </ol>
  
  <h2>Metrics</h2>
  <p>Time taken: ${metric_time_taken}s</p>
</body>
</html>
```

**Using a Custom Template:**
```bash
autoresearch search "What is quantum computing?" --output template:html
```

## Configuring Default Output Format

You can set the default output format in your `autoresearch.toml` configuration file:

```toml
[core]
output_format = "markdown"  # or "json", "plain", "template:name"
```

## Defining Custom Templates in Configuration

You can also define custom templates directly in your configuration file:

```toml
[output_templates.html]
name = "html"
description = "HTML output format"
template = """
<html>
<head><title>Autoresearch Results</title></head>
<body>
  <h1>Answer</h1>
  <p>${answer}</p>
  
  <h2>Citations</h2>
  <ul>
    ${citations}
  </ul>
  
  <h2>Reasoning</h2>
  <ol>
    ${reasoning}
  </ol>
  
  <h2>Metrics</h2>
  <p>Time taken: ${metric_time_taken}s</p>
</body>
</html>
"""
```

Then use it with:
```bash
autoresearch search "What is quantum computing?" --output template:html
```