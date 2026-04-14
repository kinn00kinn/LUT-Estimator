"""Backward-compatible script entrypoint for the LUT estimator."""

from lut_estimator.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
