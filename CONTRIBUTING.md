# Contributing

## Setup

```bash
python -m pip install -e .[dev]
```

## Development Workflow

1. Create a branch for your change.
2. Run the test suite locally.
3. Keep changes focused and include tests when behavior changes.
4. Open a pull request with a clear summary of the problem and solution.

## Tests

```bash
pytest
```

## Local Checks

```bash
pre-commit run --all-files
```

If `pytest` is not installed yet, install the development dependencies first:

```bash
python -m pip install -e .[dev]
```

## Scope

- Bug fixes are welcome.
- Refactors are welcome when they improve readability or reuse without changing behavior unexpectedly.
- Feature additions should keep the library API and CLI straightforward.
