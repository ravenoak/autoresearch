# mypy: ignore-errors
# flake8: noqa
from contextlib import contextmanager

from tests.behavior.context import BehaviorContext
import subprocess
from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, RepositoryManifestEntry
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from docx import Document
import pytest
import importlib.util
import tomli_w

pytestmark = [pytest.mark.requires_git, pytest.mark.requires_parsers]

try:
    _spec = importlib.util.find_spec("git")
    _git_available = bool(_spec and _spec.origin)
except Exception:
    _git_available = False

if not _git_available:
    pytest.skip("GitPython not installed", allow_module_level=True)


@contextmanager
def _noop_storage_connection():
    class DummyConn:
        def execute(self, *args, **kwargs):
            class Cursor:
                def fetchall(self_inner):
                    return []

            return Cursor()

    yield DummyConn()


@given("a directory with text files")
def directory_with_text_files(tmp_path, bdd_context: BehaviorContext):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "note.txt"
    file_path.write_text("hello from file")
    bdd_context["docs_dir"] = docs_dir
    bdd_context["file_path"] = file_path


@when(parsers.parse('I search the directory for "{query}"'))
def search_directory(query, monkeypatch, bdd_context: BehaviorContext):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.context_aware.enabled = False
    docs_dir = bdd_context["docs_dir"]
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("I should get results from the text files")
def check_directory_results(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    file_path = bdd_context["file_path"]
    assert any(r["url"] == str(file_path) for r in results)


@given("a directory with PDF and DOCX files")
def directory_with_pdf_docx(tmp_path, bdd_context: BehaviorContext):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    pdf_path = docs_dir / "note.pdf"
    pdf_bytes = (
        b"%PDF-1.2\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/Resources<<>>/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 24 Tf 100 700 Td (hello from pdf) Tj ET\nendstream\nendobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF"
    )
    pdf_path.write_bytes(pdf_bytes)
    docx_path = docs_dir / "note.docx"
    doc = Document()
    doc.add_paragraph("hello from docx")
    doc.save(docx_path)
    bdd_context["docs_dir"] = docs_dir
    bdd_context["pdf_path"] = pdf_path
    bdd_context["docx_path"] = docx_path


@when(parsers.parse('I search the directory for "{query}" using document parser'))
def search_directory_documents(query, monkeypatch, bdd_context: BehaviorContext):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.context_aware.enabled = False
    docs_dir = bdd_context["docs_dir"]
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["pdf", "docx"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("I should get results from the PDF and DOCX files")
def check_document_results(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    assert any(r["url"] == str(bdd_context["pdf_path"]) for r in results)
    assert any(r["url"] == str(bdd_context["docx_path"]) for r in results)


@given(parsers.parse('a local Git repository with commits containing "{term}"'))
def local_git_repository(tmp_path, bdd_context: BehaviorContext, term):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo_path, check=True)
    readme = repo_path / "README.md"
    readme.write_text(f"{term} in code")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", f"Add {term}"], cwd=repo_path, check=True)
    bdd_context["repo_path"] = repo_path
    bdd_context["term"] = term


@given(parsers.parse('a local Git repository with diffs containing "{term}"'))
def local_git_repository_with_diff(tmp_path, bdd_context: BehaviorContext, term):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo_path, check=True)
    code_file = repo_path / "code.txt"
    code_file.write_text("initial")
    subprocess.run(["git", "add", "code.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_path, check=True)
    code_file.write_text(f"initial\n{term}\n")
    subprocess.run(["git", "add", "code.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", f"Add {term}"], cwd=repo_path, check=True)
    bdd_context["repo_path"] = repo_path
    bdd_context["term"] = term


@when(parsers.parse('I search the repository for "{query}"'))
def search_repository(query, monkeypatch, bdd_context: BehaviorContext):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    repo_path = bdd_context["repo_path"]
    cfg.search.local_git.repo_path = str(repo_path)
    cfg.search.local_git.branches = ["main"]
    cfg.search.local_git.history_depth = 50
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("I should see results referencing commit messages or code")
def check_git_results(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    repo_path = bdd_context["repo_path"]
    term = bdd_context["term"]
    assert any(term in r["url"] or r["url"] == str(repo_path / "README.md") for r in results)
    assert any(r.get("commit") for r in results)


@then("I should see commit diff results with metadata")
def check_git_diff_results(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    assert any(r.get("diff") for r in results)
    assert any(r.get("author") and r.get("date") for r in results if r.get("diff"))


@then("the diff results should include surrounding code context")
def check_diff_code_context(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    term = bdd_context["term"]
    for r in results:
        if r.get("diff"):
            assert term.lower() in r["snippet"].lower()
            assert "\n" in r["snippet"]
            return
    assert False, "No diff result with context found"


@given("a repository manifest with labelled Git repositories")
def repository_manifest(tmp_path, bdd_context: BehaviorContext):
    manifest: list[dict[str, str]] = []
    query = "shared-term"
    for slug, namespace in (("alpha", "workspace.alpha"), ("beta", "workspace.beta")):
        repo_path = tmp_path / slug
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo_path, check=True)
        readme = repo_path / "README.md"
        readme.write_text(f"{slug} {query}\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", f"Add {query}"], cwd=repo_path, check=True)
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                text=True,
            )
            .strip()
        )
        manifest.append(
            {
                "slug": slug,
                "path": str(repo_path),
                "branches": [branch],
                "namespace": namespace,
            }
        )
    bdd_context["manifest"] = manifest
    bdd_context["manifest_query"] = query


@when(parsers.parse('I search the repository manifest for "{query}"'))
def search_repository_manifest(query, monkeypatch, bdd_context: BehaviorContext):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_git.manifest = [
        RepositoryManifestEntry.model_validate(entry) for entry in bdd_context["manifest"]
    ]
    cfg.search.local_git.history_depth = 50
    cfg.search.local_file.file_types = ["md", "txt"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr(StorageManager, "connection", staticmethod(_noop_storage_connection))
    bdd_context["search_results"] = Search.external_lookup(query, max_results=6)


@then("I should see manifest results grouped by repository slug")
def check_manifest_grouping(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    manifest_slugs = {entry["slug"] for entry in bdd_context["manifest"]}
    repositories = {result.get("repository") for result in results}
    assert manifest_slugs.issubset(repositories)


@then("each manifest result includes provenance metadata")
def check_manifest_provenance(bdd_context: BehaviorContext):
    results = bdd_context["search_results"]
    assert results
    for result in results:
        provenance = result.get("provenance", {})
        assert provenance.get("repository") == result.get("repository")
        if "namespace" in provenance:
            assert provenance["namespace"]


@given("a temporary manifest-aware configuration")
def temporary_manifest_configuration(tmp_path, monkeypatch, bdd_context: BehaviorContext):
    config_path = tmp_path / "autoresearch.toml"
    config_payload = {
        "core": {"loops": 1},
        "search": {
            "backends": ["local_git"],
            "context_aware": {"enabled": False},
            "local_git": {"history_depth": 50, "manifest": []},
        },
    }
    config_path.write_text(tomli_w.dumps(config_payload), encoding="utf-8")
    loader = ConfigLoader.new_for_tests(search_paths=[config_path])
    monkeypatch.setattr("autoresearch.main.app._config_loader", loader, raising=False)
    bdd_context["config_path"] = config_path
    bdd_context["config_loader"] = loader


@given("the following repositories are available for manifest CLI management:")
def manifest_cli_repositories(tmp_path, table, bdd_context: BehaviorContext):
    query = "shared-term"
    repos: list[dict[str, object]] = []
    for row in table:
        slug = row["slug"]
        namespace = row["namespace"]
        repo_path = tmp_path / slug
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo_path, check=True)
        readme = repo_path / "README.md"
        readme.write_text(f"{slug} {query}\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", f"Add {query}"], cwd=repo_path, check=True)
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                text=True,
            )
            .strip()
        )
        repos.append(
            {
                "slug": slug,
                "namespace": namespace,
                "path": repo_path,
                "branch": branch,
            }
        )
    bdd_context["manifest_repos"] = repos
    bdd_context["manifest_query"] = query


@when("I add the repositories to the manifest via the CLI")
def add_repositories_via_cli(cli_runner, cli_app, bdd_context: BehaviorContext):
    for entry in bdd_context["manifest_repos"]:
        args = [
            "search",
            "manifest",
            "add",
            str(entry["path"]),
            "--slug",
            entry["slug"],
            "--branch",
            entry["branch"],
        ]
        namespace = entry.get("namespace")
        if namespace:
            args.extend(["--namespace", namespace])
        result = cli_runner.invoke(cli_app, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output


@when(parsers.parse('I update manifest slug "{slug}" to namespace "{namespace}" via the CLI'))
def update_manifest_via_cli(slug: str, namespace: str, cli_runner, cli_app) -> None:
    result = cli_runner.invoke(
        cli_app,
        ["search", "manifest", "update", slug, "--namespace", namespace],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output


@when(parsers.parse('I remove manifest slug "{slug}" via the CLI'))
def remove_manifest_via_cli(slug: str, cli_runner, cli_app) -> None:
    result = cli_runner.invoke(
        cli_app, ["search", "manifest", "remove", slug], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output


@when("I list the manifest via the CLI")
def list_manifest_via_cli(cli_runner, cli_app, bdd_context: BehaviorContext):
    result = cli_runner.invoke(
        cli_app, ["search", "manifest", "list"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    bdd_context["manifest_cli_output"] = result.stdout


@then("the manifest CLI output lists:")
def verify_manifest_cli_output(table, bdd_context: BehaviorContext):
    output = bdd_context.get("manifest_cli_output", "")
    assert output, "Manifest CLI output was empty"
    expected_slugs = {row["slug"] for row in table}
    for row in table:
        slug = row["slug"]
        namespace = row["namespace"]
        assert slug in output
        if namespace:
            assert namespace in output
    removed = {
        entry["slug"]
        for entry in bdd_context.get("manifest_repos", [])
        if entry["slug"] not in expected_slugs
    }
    for slug in removed:
        assert slug not in output


@then(parsers.parse('a manifest-backed search for "{query}" returns provenance from:'))
def verify_manifest_provenance_from_cli(
    query: str,
    table,
    monkeypatch,
    bdd_context: BehaviorContext,
):
    loader: ConfigLoader = bdd_context["config_loader"]
    cfg = loader.load_config().model_copy(update={"loops": 1})
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr(StorageManager, "connection", staticmethod(_noop_storage_connection))
    results = Search.external_lookup(query, max_results=6)
    expected = {(row["slug"], row["namespace"]) for row in table}
    expected_slugs = {row["slug"] for row in table}
    actual: set[tuple[str, str | None]] = set()
    for result in results:
        slug = result.get("repository")
        provenance = result.get("provenance", {})
        namespace = provenance.get("namespace")
        if slug in expected_slugs:
            actual.add((slug, namespace))
    assert expected <= actual
    removed = {
        entry["slug"]
        for entry in bdd_context.get("manifest_repos", [])
        if entry["slug"] not in expected_slugs
    }
    for result in results:
        assert result.get("repository") not in removed
    ConfigLoader.reset_instance()


@scenario("../features/local_sources.feature", "Searching a directory for text files")
def test_search_directory(bdd_context: BehaviorContext):
    assert bdd_context["search_results"]


@scenario(
    "../features/local_sources.feature",
    "Searching a local Git repository for code snippets or commit messages",
)
def test_search_git_repo(bdd_context: BehaviorContext):
    assert bdd_context["search_results"]


@scenario("../features/local_sources.feature", "Searching a directory for PDF and DOCX files")
def test_search_document_directory(bdd_context: BehaviorContext):
    assert bdd_context["search_results"]


@scenario(
    "../features/local_sources.feature",
    "Searching commit diffs and metadata in a local Git repository",
)
def test_search_git_diffs(bdd_context: BehaviorContext):
    assert bdd_context["search_results"]


@scenario(
    "../features/local_sources.feature",
    "Searching commit diffs with code context",
)
def test_search_git_diff_context(bdd_context: BehaviorContext):
    assert bdd_context["search_results"]
