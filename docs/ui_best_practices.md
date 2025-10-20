# UI/UX Best Practices

This document provides practical guidance for implementing UI/UX features in
Autoresearch, focusing on when to use specific patterns and how to maintain
consistency.

## When to Use Different Output Formats

### Console Format (Human-Readable)
**Use when**:
- Interactive terminal usage
- Users need to read and understand output immediately
- Debugging or troubleshooting
- Presentation to stakeholders

**Format**: `[LEVEL] component: message [correlation_id]`
**Example**:
```bash
[INFO] search.core: Processing query in 2.3s [req-12345]
[WARNING] llm.adapter: Model response truncated [req-12345]
```

### JSON Format (Machine-Parseable)
**Use when**:
- Automation and scripting
- Log aggregation systems
- Programmatic consumption
- CI/CD pipelines
- Data analysis workflows

**Format**: Structured JSON with consistent schema
**Example**:
```json
{
  "timestamp": "2025-10-15T14:30:45.123Z",
  "level": "INFO",
  "logger": "search.core",
  "message": "Processing query in 2.3s",
  "correlation_id": "req-12345",
  "query_length": 42
}
```

### Bare Mode (Accessibility)
**Use when**:
- Screen reader users
- Simplified interfaces needed
- Text-only environments
- Compliance with accessibility standards

**Format**: Plain text with descriptive labels
**Example**:
```
INFO: search.core: Processing query in 2.3s
WARNING: llm.adapter: Model response truncated
```

## Implementing New UI Components

### Component Design Principles

1. **Single Responsibility**: Each component should have one clear purpose
2. **Consistent Interface**: Follow established patterns for options and output
3. **Error Handling**: Provide clear, actionable error messages
4. **Accessibility**: Support keyboard navigation and screen readers
5. **Testing**: Include comprehensive BDD tests

### Component Structure Template

```python
class NewComponent:
    """Brief description of component purpose."""
    
    def __init__(self, config: ConfigModel):
        """Initialize component with configuration."""
        self.config = config
        self.logger = get_logger(__name__)
    
    def render(self, data: Any) -> str:
        """Render component output.
        
        Args:
            data: Input data to render
            
        Returns:
            Formatted output string
        """
        # Implementation
        return formatted_output
    
    def validate_input(self, data: Any) -> None:
        """Validate input data and raise appropriate errors."""
        if not data:
            raise ValidationError("Input data is required")
```

### Testing New Components

**BDD Feature Structure**:
```gherkin
Feature: New Component Functionality
  As a user of the new component
  I want to perform specific operations
  So that I can achieve my goals

  Scenario: Basic operation
    Given the component is configured
    When I provide valid input
    Then I should receive expected output

  Scenario: Error handling
    Given the component is configured
    When I provide invalid input
    Then I should receive a clear error message
    And the error should include actionable suggestions
```

## Error Handling Best Practices

### Error Message Guidelines

1. **Be Specific**: Clearly state what went wrong
2. **Provide Context**: Include where and when the error occurred
3. **Offer Solutions**: Suggest specific actions the user can take
4. **Include Examples**: Show correct usage when applicable
5. **Maintain Consistency**: Use the same format across all interfaces

### Error Categories and Responses

| Error Type | Example Message | Suggested Action |
|------------|----------------|------------------|
| Configuration | "Invalid log format" | "Valid options: json/console/auto" |
| Network | "Connection failed to LM Studio" | "Confirm LM Studio is running" |
| Validation | "Query cannot be empty" | "Provide a non-empty query string" |
| Permission | "Access denied to database" | "Check file permissions" |
| Resource | "Out of memory" | "Trim query size or add memory" |

### Error Code Standards

- **1xx**: Configuration errors (invalid settings, missing files)
- **2xx**: Network errors (connection failures, API issues)
- **3xx**: Data errors (invalid input, format issues)
- **4xx**: Permission errors (access denied, authentication)
- **5xx**: System errors (resource exhaustion, internal failures)

## Accessibility Implementation

### Keyboard Navigation

**Requirements**:
- All functionality accessible via keyboard
- Logical tab order (top to bottom, left to right)
- Visible focus indicators
- Skip links for main content

**Implementation**:
Use a dedicated `DepthSelector` (see Integrating Shared UX Standards in Qt).
```python
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QPushButton,
    QShortcut,
    QWidget,
)
from autoresearch.output_format import OutputDepth


class QueryPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.query_input = QLineEdit(self)
        self.depth_selector = DepthSelector(self)
        self.submit_button = QPushButton("Run Query", self)

        layout = QFormLayout(self)
        layout.addRow("Query", self.query_input)
        layout.addRow("Depth", self.depth_selector)
        layout.addRow(self.submit_button)

        self.setTabOrder(self.query_input, self.depth_selector)
        self.setTabOrder(self.depth_selector, self.submit_button)

        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_results)
        self.submit_button.clicked.connect(self.run_query)
        self.depth_selector.depthChanged.connect(self.update_depth_hint)

    def save_results(self) -> None:
        ...

    def run_query(self) -> None:
        ...

    def update_depth_hint(self, depth: OutputDepth) -> None:
        ...
```

### Screen Reader Support

**Requirements**:
- Semantic HTML structure
- Proper heading hierarchy
- Alt text for images
- ARIA labels for complex widgets

**Implementation**:
```python
from PySide6.QtGui import QAccessible
from PySide6.QtWidgets import QLabel

result_header = QLabel("Query Results", parent)
result_header.setAccessibleName("Query results heading")
result_header.setAccessibleDescription(
    "Summary of the current query execution."
)

chart_view = PerformanceChart(parent)
chart_view.setAccessibleName("Query performance chart")
chart_view.setAccessibleDescription(
    "Bar chart comparing response times across depth levels."
)

depth_selector.setAccessibleName("Depth level")
depth_selector.setAccessibleDescription(
    "Choose TL;DR, Concise, Standard, or Trace summarization depth."
)
depth_selector.currentIndexChanged.connect(
    lambda _: QAccessible.updateAccessibility()
)
```

### Color and Contrast

**Requirements**:
- WCAG 2.1 AA compliance (4.5:1 ratio for normal text)
- No reliance on color alone for information
- High contrast mode support

**Implementation**:
```python
from PySide6.QtGui import QColor, QPalette

palette = window.palette()
palette.setColor(QPalette.WindowText, QColor("#1b1b1f"))
palette.setColor(QPalette.Highlight, QColor("#1c7c54"))
palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
window.setPalette(palette)

window.setStyleSheet(
    """
    QPushButton.success {
        background-color: #1c7c54;
        color: #ffffff;
    }
    QPushButton.warning {
        background-color: #b38728;
        color: #101010;
    }
    QPushButton.error {
        background-color: #a12830;
        color: #ffffff;
    }
    """
)

status_label.setText(f"Error: {error_message}")
status_label.setProperty("state", "error")
status_label.setAccessibleDescription(
    "Error message with high-contrast styling."
)
```

## Performance Optimization

### Response Time Guidelines

| Operation | Target Time | User Feedback |
|-----------|-------------|---------------|
| Initial feedback | < 2 seconds | Show loading indicator |
| Progress updates | Every 1-2 seconds | Update progress bar |
| Query completion | < 30 seconds | Show completion message |
| Large result rendering | < 5 seconds | Show rendering progress |

### Memory Management

**Guidelines**:
- Process large datasets in chunks
- Implement pagination for large result sets
- Use streaming for real-time updates
- Monitor and log memory usage

**Implementation**:
```python
def process_large_dataset(data: list) -> Iterator[dict]:
    """Process large dataset in memory-efficient chunks."""
    chunk_size = 1000
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield from process_chunk(chunk)
        
        # Force garbage collection if needed
        if i % 10000 == 0:
            import gc
            gc.collect()
```

### UI Responsiveness

**Guidelines**:
- Keep UI responsive during long operations
- Show progress indicators for operations > 2 seconds
- Allow cancellation of long-running operations
- Provide feedback on operation status

**Implementation**:
```python
from PySide6.QtCore import QObject, QThread, Signal


class QueryWorker(QObject):
    finished = Signal(QueryResult)
    progress = Signal(int)
    failed = Signal(str)

    def __init__(self, query: str) -> None:
        super().__init__()
        self._query = query

    def run(self) -> None:
        try:
            for percent in execute_query(self._query):
                self.progress.emit(percent)
            self.finished.emit(load_results())
        except QueryError as exc:
            self.failed.emit(str(exc))


worker = QueryWorker(query)
thread = QThread(window)
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(show_results)
worker.progress.connect(progress_bar.setValue)
worker.failed.connect(show_error)

cancel_button.clicked.connect(thread.requestInterruption)
thread.start()
```

## Cross-Interface Consistency

### Command Structure

**CLI Commands**:
```bash
# Consistent structure
autoresearch <command> [global-options] [command-options] <arguments>

# Examples
autoresearch search --depth standard --include metrics "query"
autoresearch config validate --format json
autoresearch backup create --output backup.zip
```

**API Endpoints**:
```http
# RESTful naming
GET /api/v1/capabilities
POST /api/v1/query
PUT /api/v1/config
```

### Response Formats

**Consistent Schema**:
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "correlation_id": "req-12345",
    "timestamp": "2025-10-15T14:30:45Z",
    "version": "1.0"
  },
  "errors": [...]
}
```

### Error Handling

**Consistent Error Format**:
```json
{
  "error": {
    "code": "CONFIG_INVALID",
    "message": "Invalid configuration setting",
    "suggestion": "Check the configuration file syntax",
    "example": "autoresearch config validate"
  },
  "metadata": {
    "correlation_id": "req-12345",
    "timestamp": "2025-10-15T14:30:45Z"
  }
}
```

## Integrating Shared UX Standards in Qt

### Progressive Disclosure with Depth Levels

The CLI, API, and PySide6 surfaces must expose the same progressive
disclosure depths so users always know how much detail to expect. Reuse the
enumerations in `autoresearch.output_format` instead of redefining widget
options.

```python
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QWidget
from autoresearch.output_format import OutputDepth


class DepthSelector(QComboBox):
    depthChanged = Signal(OutputDepth)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        for depth in OutputDepth:
            self.addItem(depth.label, userData=depth)
        self.currentIndexChanged.connect(self._emit_depth)

    def _emit_depth(self, index: int) -> None:
        depth = self.itemData(index)
        if depth is not None:
            self.depthChanged.emit(depth)
```

Use the shared depth metadata to progressively disclose panels and hints.

```python
from PySide6.QtWidgets import QWidget
from autoresearch.output_format import (
    OutputDepth,
    describe_depth_features,
)


class DepthAwarePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._features = describe_depth_features()
        self.claim_panel.hide()
        self.trace_panel.hide()
        self.graph_panel.hide()
        self.knowledge_panel.hide()

    def bind_selector(self, selector: DepthSelector) -> None:
        selector.depthChanged.connect(self.apply_depth)

    def apply_depth(self, depth: OutputDepth) -> None:
        features = self._features[depth]
        self.claim_panel.setVisible(features["claim_audits"])
        self.trace_panel.setVisible(features["full_trace"])
        self.graph_panel.setVisible(features["graph_exports"])
        self.knowledge_panel.setVisible(features["knowledge_graph"])
```

#### Operational Considerations

- Mirror CLI microcopy when displaying depth labels and tooltips.
- Emit telemetry whenever a depth change occurs to keep analytics aligned.
- Provide contextual help (e.g., "Trace depth includes raw payloads") by
  reading `OutputDepth.description`.

## Testing Best Practices

### BDD Testing Structure

**Feature Organization**:
- Group related scenarios in feature files
- Use descriptive scenario names
- Include both positive and negative test cases
- Test edge cases and error conditions

**Step Implementation**:
```python
@when("I run autoresearch search with invalid configuration")
def step_run_search_invalid_config(context: BehaviorContext) -> None:
    """Run search command with invalid configuration."""
    runner = CliRunner()
    # Mock invalid configuration
    with patch.dict(os.environ, {"AUTORESEARCH_CONFIG": "/invalid/path"}):
        result = runner.invoke(cli_app, ["search", "test query"])
        set_value(context, "cli_result", result)
```

### Accessibility Testing

**Automated Testing**:
```python
def test_color_contrast():
    """Test that colors meet WCAG 2.1 AA requirements."""
    # Use color contrast checking libraries
    from colour import Color
    
    success_color = Color("#28a745")
    background_color = Color("#ffffff")
    
    contrast_ratio = success_color.contrast(background_color)
    assert contrast_ratio >= 4.5, f"Insufficient contrast: {contrast_ratio}"
```

**Manual Testing Checklist**:
- [ ] Navigate entire interface using only keyboard
- [ ] Test with screen reader (NVDA, JAWS, VoiceOver)
- [ ] Verify color contrast ratios
- [ ] Check alt text for all images
- [ ] Test with high contrast mode

### Performance Testing

**Load Testing**:
```python
def test_concurrent_queries():
    """Test system performance under concurrent load."""
    import concurrent.futures
    
    def run_query(query_id: int) -> float:
        start_time = time.time()
        # Run query
        end_time = time.time()
        return end_time - start_time
    
    # Test with multiple concurrent queries
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_query, i) for i in range(100)]
        response_times = [future.result() for future in futures]
        
        # Verify performance requirements
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 5.0, f"Average response time too slow: {avg_time}s"
```

## Documentation Best Practices

### User Documentation

**Structure**:
1. **Getting Started**: Quick setup and first use
2. **Tutorials**: Step-by-step guides for common tasks
3. **Reference**: Complete command and API documentation
4. **Troubleshooting**: Common issues and solutions
5. **FAQ**: Frequently asked questions

**Content Guidelines**:
- Use simple, clear language
- Include practical examples
- Provide context for technical concepts
- Update regularly with new features

### Developer Documentation

**Code Documentation**:
- Docstrings for all public functions
- Type hints for all parameters
- Usage examples in docstrings
- Architecture decision records

**Design Documentation**:
- Component interaction diagrams
- State management patterns
- Error handling flows
- Performance considerations

## Continuous Improvement

### User Feedback Collection

**Methods**:
- In-app feedback forms
- User interviews and surveys
- Support ticket analysis
- Usage analytics

**Implementation**:
```python
# Optional feedback collection
if user_consent_given():
    track_feature_usage("new_ui_feature")
    collect_feedback("How easy was this feature to use?")
```

### Regular Reviews

**Quarterly Process**:
1. **User Experience Review**: Analyze feedback and usage patterns
2. **Technical Review**: Evaluate performance and maintainability
3. **Accessibility Audit**: Verify compliance with standards
4. **Documentation Review**: Update guides and examples

**Action Items**:
- Prioritize improvements based on user impact
- Implement changes incrementally
- Test thoroughly before deployment
- Document all changes and rationale

## Appendix A: Streamlit Guidance (Deprecated)

Streamlit examples remain for legacy maintenance only. Review the
[PySide6 Migration and Streamlit Removal Plan](pyside6_migration_plan.md) for
sunset milestones before touching these snippets.

```python
# Legacy accessibility hook
st.markdown("<h1>Query Results</h1>", unsafe_allow_html=True)
st.image("chart.png", caption="Query performance chart")
depth = st.selectbox(
    "Select depth level",
    options=["TLDR", "Concise", "Standard", "Trace"],
    key="depth_selector",
)
```

```python
# Legacy color messaging
success_color = "#28a745"
warning_color = "#ffc107"
error_color = "#dc3545"

if color_indicates_error:
    st.error(f"Error: {error_message}")
```

```python
# Legacy long-running task handling
with st.spinner("Processing query..."):
    result = run_query(query)

if st.button("Cancel"):
    cancel_operation()
    st.info("Operation cancelled")
```

## Conclusion

These best practices provide a foundation for consistent, accessible, and
maintainable UI/UX implementation in Autoresearch. By following these
guidelines, developers can create interfaces that are both functional and
delightful to use while ensuring long-term maintainability and accessibility.

Remember: Good UI/UX is iterative. Start with core functionality, gather
feedback, and continuously improve based on real user needs and usage
patterns.
