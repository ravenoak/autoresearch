from autoresearch.logging_utils import configure_logging, get_logger


def test_get_logger():
    configure_logging()
    log = get_logger("test")
    assert hasattr(log, "info")
    log.info("message")
