# LUT Estimator

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)

Estimate a 3D LUT from a pair of images and apply that look to another image. The project is packaged as a small Python library with a CLI, so it is easier to reuse in scripts, experiments, and OSS workflows.

<p align="center">
  <img src="img/base.JPG" width="400" alt="Original image">
</p>

<p align="center"><b>Original image</b></p>

<p align="center">
  <img src="img/apply_lut.JPG" width="400" alt="Reference image with grading applied">
</p>

<p align="center"><b>Reference image with grading applied</b></p>

<p align="center">
  <img src="apply_estimated_lut.jpg" width="400" alt="Image processed with the estimated LUT">
</p>

<p align="center"><b>Image processed with the estimated LUT</b></p>

## Features

- Estimates a 3D LUT from before/after image pairs using a two-stage interpolation strategy.
- Applies LUTs with trilinear interpolation to reduce banding artifacts.
- Supports optional Gaussian blur before estimation to stabilize noisy inputs.
- Exports the estimated LUT as a standard `.cube` file.
- Provides both a Python API and a command-line interface.

## Installation

Clone the repository and install it in editable mode:

```bash
python -m pip install -e .[dev]
```

If you only need runtime dependencies:

```bash
python -m pip install -e .
```

## Quick Start

Run the CLI with a before/after pair and a target image:

```bash
lut-estimator \
  --before img/base.JPG \
  --after img/apply_lut.JPG \
  --target img/base.JPG \
  --output estimated_result.jpg \
  --lut-size 33 \
  --sample-rate 0.02 \
  --blur-ksize 0
```

This writes:

- The transformed image to `estimated_result.jpg`
- A companion LUT file to `estimated_result.cube` unless `--no-cube` is passed

You can also keep using the legacy script entrypoint:

```bash
python lut_tool.py --before img/base.JPG --after img/apply_lut.JPG --target img/base.JPG
```

## Python API

```python
from lut_estimator import estimate_and_apply_lut

estimate_and_apply_lut(
    before_image_path="img/base.JPG",
    after_image_path="img/apply_lut.JPG",
    target_image_path="img/base.JPG",
    output_image_path="estimated_result.jpg",
    lut_size=33,
    sample_rate=0.02,
    blur_ksize=0,
    save_cube=True,
    seed=42,
)
```

## Parameters

- `lut_size`: LUT grid resolution. Larger values are more accurate but slower.
- `sample_rate`: Fraction of pixels used for LUT estimation.
- `blur_ksize`: Odd Gaussian kernel size used before estimation. Set `0` to disable blur.
- `seed`: Optional random seed for reproducible sampling.

## Development

Run tests with:

```bash
pytest
```

## Project Structure

```text
src/lut_estimator/
  core.py      Core LUT estimation and application logic
  cli.py       Command-line interface
tests/
  test_core.py Minimal regression tests
lut_tool.py    Backward-compatible entrypoint
```

## Notes

- Input images are expected to be aligned before/after pairs.
- If the before/after images have different sizes, both are resized to the smaller common resolution for estimation.
- The current estimator assumes an RGB-to-RGB global color transform rather than localized edits.

## License

Released under the MIT License.
