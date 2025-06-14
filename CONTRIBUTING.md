# Contributing

Thank you for considering a contribution! Follow these steps to set up the development environment and run the test suite.

1. Install the dependencies:
   ```bash
   poetry install --with dev
   ```
   Alternatively you can execute the helper script:
   ```bash
   ./scripts/setup.sh
   ```
   If you prefer pip, run `pip install -e .` instead.

2. Lint and type check the code:
   ```bash
   poetry run flake8 src tests
   poetry run mypy src
   ```

3. Run the tests:
   ```bash
   poetry run pytest
   poetry run pytest tests/behavior
   ```

4. Remove Python cache directories:
   ```bash
   task clean
   ```

Please keep commits focused and descriptive.
