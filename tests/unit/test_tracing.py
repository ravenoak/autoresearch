from autoresearch import tracing


def test_setup_tracing_idempotent():
    tracing._tracer_provider = None
    tracing.setup_tracing(True)
    first = tracing._tracer_provider
    tracing.setup_tracing(True)
    assert tracing._tracer_provider is first
    assert tracing.get_tracer("t")
    if tracing._tracer_provider:
        tracing._tracer_provider.shutdown()
    tracing._tracer_provider = None


def test_setup_tracing_disabled():
    tracing._tracer_provider = None
    tracing.setup_tracing(False)
    assert tracing._tracer_provider is None
