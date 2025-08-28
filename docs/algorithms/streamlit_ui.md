# Streamlit UI

Utility functions customize the web UI through Streamlit session state.
`apply_accessibility_settings` injects high-contrast CSS when users enable
`high_contrast`, while `apply_theme_settings` toggles light and dark themes based
on the `dark_mode` flag. `display_guided_tour` and `display_help_sidebar`
introduce onboarding elements that disappear after user acknowledgement.

## Simulation

The snippet below demonstrates theme toggling without launching Streamlit:

```python
from unittest.mock import Mock
import streamlit_ui as ui

st = Mock()
st.session_state = {"dark_mode": True}
ui.st = st  # monkeypatch
ui.apply_theme_settings()
assert "background-color:#1c1c1c" in st.markdown.call_args[0][0]
```

## References

- [`streamlit_ui.py`](../../src/autoresearch/streamlit_ui.py)
- Streamlit session state guide[^st]

[^st]: https://docs.streamlit.io/library/api-reference/session-state
