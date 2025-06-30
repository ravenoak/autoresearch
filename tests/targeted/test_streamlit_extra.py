import types

from autoresearch import streamlit_app  # noqa: E402


def test_apply_accessibility(monkeypatch):
    calls = []
    fake_st = types.SimpleNamespace(markdown=lambda *a, **k: calls.append(a))
    fake_st.session_state = {'high_contrast': True}
    monkeypatch.setattr(streamlit_app, 'st', fake_st)
    streamlit_app.apply_accessibility_settings()
    assert len(calls) == 2


def test_display_query_input_has_accessibility(monkeypatch):
    calls = {"markdown": [], "button": []}

    class Dummy:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            pass

    fake_st = types.SimpleNamespace(
        markdown=lambda *a, **k: calls["markdown"].append((a, k)),
        text_area=lambda *a, **k: "",
        selectbox=lambda *a, **k: None,
        slider=lambda *a, **k: 0,
        button=lambda *a, **k: calls["button"].append(k) or False,
        columns=lambda *a, **k: (Dummy(), Dummy()),
        container=lambda: Dummy(),
        session_state={"config": types.SimpleNamespace(reasoning_mode=streamlit_app.ReasoningMode.DIALECTICAL, loops=2)}
    )
    monkeypatch.setattr(streamlit_app, "st", fake_st)
    streamlit_app.display_query_input()
    assert any("aria-label='Query input area'" in args[0] for args, _ in calls["markdown"])
    assert any("run your query" in kw.get("help", "") for kw in calls["button"])
