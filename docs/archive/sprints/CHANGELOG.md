name: MOVRvest CI

on:
  push:
    branches:
      - main
      - master
      - develop
      - feature/**
  pull_request:

jobs:
  quality:
    name: Quality Checks
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pre-commit
          pip install pytest pytest-cov ruff mypy

      - name: Run pre-commit hooks
        run: |
          pre-commit run --all-files

      - name: Run test suite
        run: |
          pytest