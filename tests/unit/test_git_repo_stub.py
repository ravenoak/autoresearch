import pytest
from git import Repo
from pathlib import Path


@pytest.mark.requires_git
def test_repo_init_and_commit(tmp_path: Path) -> None:
    """Ensure the git.Repo stub can initialize and commit."""
    repo = Repo.init(tmp_path)
    commit = repo.index.commit("init")
    assert repo.head.commit == commit
    assert commit.message == "init"
