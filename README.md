# LUT Estimator

[![PyPI](https://img.shields.io/pypi/v/lut-estimator.svg)](https://pypi.org/project/lut-estimator/)
[![GitHub](https://img.shields.io/badge/github-kinn00kinn%2FLUT--Estimator-24292f.svg)](https://github.com/kinn00kinn/LUT-Estimator)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://pypi.org/project/lut-estimator/)

Estimate a 3D LUT from a before/after image pair and apply that look to another image.
The package is published on PyPI and can be used either as a CLI tool or as a small Python library.

Japanese documentation is available in `README.ja.md`.

## Why This Exists

This project is for cases where you have:

- a source image before grading
- a reference image after grading
- another target image that should receive a similar look

The estimator samples the before/after pair, reconstructs a 3D LUT, and applies that LUT to the target image with trilinear interpolation.

## Example Result

<p align="center">
  <img src="https://raw.githubusercontent.com/kinn00kinn/LUT-Estimator/main/img/base.JPG" width="30%" alt="Input image before grading">
  <img src="https://raw.githubusercontent.com/kinn00kinn/LUT-Estimator/main/img/apply_lut.JPG" width="30%" alt="Reference image after grading">
  <img src="https://raw.githubusercontent.com/kinn00kinn/LUT-Estimator/main/apply_estimated_lut.jpg" width="30%" alt="Image processed with the estimated LUT">
</p>

<p align="center">
  <em>Left: source image, center: reference grading, right: target processed with the estimated LUT</em>
</p>

## Features

- Estimates a 3D LUT from aligned before/after image pairs
- Applies LUTs with trilinear interpolation to reduce banding
- Supports optional Gaussian blur before estimation
- Exports the estimated LUT as a standard `.cube` file
- Provides both a CLI and a Python API

## Install

Install from PyPI:

```bash
python -m pip install lut-estimator
```

After installation, you can:

- run the `lut-estimator` command from your shell
- import `lut_estimator` from Python

For development from source:

```bash
python -m pip install -e .[dev]
```

## CLI Usage

Basic usage:

```bash
lut-estimator \
  --before before.jpg \
  --after after.jpg \
  --target target.jpg \
  --output estimated_result.jpg
```

Example with tuning parameters:

```bash
lut-estimator \
  --before img/base.JPG \
  --after img/apply_lut.JPG \
  --target img/base.JPG \
  --output estimated_result.jpg \
  --lut-size 33 \
  --sample-rate 0.02 \
  --blur-ksize 0 \
  --seed 42
```

This writes:

- the transformed image to the path given by `--output`
- a companion `.cube` LUT file unless `--no-cube` is passed

Show CLI help:

```bash
lut-estimator --help
```

Legacy script entrypoint:

```bash
python lut_tool.py --before before.jpg --after after.jpg --target target.jpg
```

## Python Usage

```python
from lut_estimator import estimate_and_apply_lut

estimate_and_apply_lut(
    before_image_path="before.jpg",
    after_image_path="after.jpg",
    target_image_path="target.jpg",
    output_image_path="estimated_result.jpg",
    lut_size=33,
    sample_rate=0.02,
    blur_ksize=0,
    save_cube=True,
    seed=42,
)
```

## Parameters

- `lut_size`: LUT grid resolution. Larger values are usually more accurate but slower.
- `sample_rate`: Fraction of pixels used for LUT estimation.
- `blur_ksize`: Odd Gaussian kernel size used before estimation. Set `0` to disable blur.
- `seed`: Optional random seed for reproducible sampling.

## Project Layout

```text
src/lut_estimator/
  core.py      Core LUT estimation and application logic
  cli.py       Command-line interface
tests/
  test_core.py Regression tests
lut_tool.py    Backward-compatible script entrypoint
```

## Notes

- Input images should be aligned before/after pairs.
- If the before/after images differ in size, both are resized to the smaller common resolution for estimation.
- The current estimator models a global RGB-to-RGB transform rather than localized retouching.

## Development

Run tests:

```bash
pytest
```

Install pre-commit hooks:

```bash
pre-commit install
```

Build distributions:

```bash
python -m build --no-isolation
```

Validate package metadata:

```bash
python -m twine check dist/*
```

## Community

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Release notes: [CHANGELOG.md](CHANGELOG.md)
- Release procedure: [RELEASE.md](RELEASE.md)

## License

Released under the MIT License.
