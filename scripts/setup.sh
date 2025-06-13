#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
pip install poetry
poetry install --with dev
poetry run pip install networkx duckdb rdflib
