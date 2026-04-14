from __future__ import annotations

import argparse

from .core import estimate_and_apply_lut


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lut-estimator",
        description="Estimate a 3D LUT from a before/after image pair and apply it to a target image.",
    )
    parser.add_argument("--before", required=True, help="Path to the source image before grading.")
    parser.add_argument("--after", required=True, help="Path to the reference image after grading.")
    parser.add_argument("--target", required=True, help="Path to the target image to transform.")
    parser.add_argument("--output", default="estimated_output.png", help="Path to the output image.")
    parser.add_argument("--lut-size", type=int, default=33, help="LUT grid size. Default: 33.")
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=0.01,
        help="Fraction of pixels sampled from the before/after pair. Default: 0.01.",
    )
    parser.add_argument(
        "--blur-ksize",
        type=int,
        default=5,
        help="Gaussian blur kernel size used before estimation. Use 0 to disable. Default: 5.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible sampling.")
    parser.add_argument(
        "--no-cube",
        action="store_true",
        help="Disable writing a companion .cube file next to the output image.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = estimate_and_apply_lut(
        before_image_path=args.before,
        after_image_path=args.after,
        target_image_path=args.target,
        output_image_path=args.output,
        lut_size=args.lut_size,
        sample_rate=args.sample_rate,
        blur_ksize=args.blur_ksize,
        save_cube=not args.no_cube,
        seed=args.seed,
    )

    print(f"Saved output image to {result['output_image']}")
    if result["cube_path"]:
        print(f"Saved LUT cube to {result['cube_path']}")
    print(f"Completed in {result['elapsed_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
