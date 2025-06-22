# flake8: noqa
import subprocess
from pytest_bdd import scenario, given, when, then, parsers

from .common_steps import *  # noqa: F401,F403
from autoresearch.config import ConfigModel
from autoresearch.search import Search
from pdfminer.high_level import extract_text
from docx import Document


@given("a directory with text files")
def directory_with_text_files(tmp_path, bdd_context):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "note.txt"
    file_path.write_text("hello from file")
    bdd_context["docs_dir"] = docs_dir
    bdd_context["file_path"] = file_path




@when(parsers.parse('I search the directory for "{query}"'))
def search_directory(query, monkeypatch, bdd_context):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.context_aware.enabled = False
    docs_dir = bdd_context["docs_dir"]
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("I should get results from the text files")
def check_directory_results(bdd_context):
    results = bdd_context["search_results"]
    file_path = bdd_context["file_path"]
    assert any(r["url"] == str(file_path) for r in results)


@given("a directory with PDF and DOCX files")
def directory_with_pdf_docx(tmp_path, bdd_context):
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
def search_directory_documents(query, monkeypatch, bdd_context):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.context_aware.enabled = False
    docs_dir = bdd_context["docs_dir"]
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["pdf", "docx"]
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("I should get results from the PDF and DOCX files")
def check_document_results(bdd_context):
    results = bdd_context["search_results"]
    assert any(r["url"] == str(bdd_context["pdf_path"]) for r in results)
    assert any(r["url"] == str(bdd_context["docx_path"]) for r in results)


@given(parsers.parse('a local Git repository with commits containing "{term}"'))
def local_git_repository(tmp_path, bdd_context, term):
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
def local_git_repository_with_diff(tmp_path, bdd_context, term):
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
def search_repository(query, monkeypatch, bdd_context):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    repo_path = bdd_context["repo_path"]
    cfg.search.local_git.repo_path = str(repo_path)
    cfg.search.local_git.branches = ["main"]
    cfg.search.local_git.history_depth = 50
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("I should see results referencing commit messages or code")
def check_git_results(bdd_context):
    results = bdd_context["search_results"]
    repo_path = bdd_context["repo_path"]
    term = bdd_context["term"]
    assert any(term in r["url"] or r["url"] == str(repo_path / "README.md") for r in results)
    assert any(r.get("commit") for r in results)


@then("I should see commit diff results with metadata")
def check_git_diff_results(bdd_context):
    results = bdd_context["search_results"]
    assert any(r.get("diff") for r in results)
    assert any(r.get("author") and r.get("date") for r in results if r.get("diff"))


@scenario("../features/local_sources.feature", "Searching a directory for text files")
def test_search_directory():
    pass


@scenario(
    "../features/local_sources.feature",
    "Searching a local Git repository for code snippets or commit messages",
)
def test_search_git_repo():
    pass


@scenario("../features/local_sources.feature", "Searching a directory for PDF and DOCX files")
def test_search_document_directory():
    pass


@scenario(
    "../features/local_sources.feature",
    "Searching commit diffs and metadata in a local Git repository",
)
def test_search_git_diffs():
    pass
