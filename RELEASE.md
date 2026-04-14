# Release Guide

## 1. Update version

Update the version in `pyproject.toml` and add an entry to `CHANGELOG.md`.

## 2. Build distributions

```bash
python -m pip install --upgrade build twine
python -m build
```

## 3. Validate package metadata

```bash
python -m twine check dist/*
```

## 4. Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

## 5. Upload to PyPI

```bash
python -m twine upload dist/*
```

## Notes

- Confirm the package name is available on PyPI before the first release.
- Use a PyPI API token rather than a password.
- Tag the release in Git after the upload succeeds.
