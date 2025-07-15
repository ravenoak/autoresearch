from autoresearch.cli_helpers import find_similar_commands


def test_find_similar_commands_basic():
    cmds = ["search", "serve", "backup"]
    matches = find_similar_commands("serch", cmds)
    assert "search" in matches
