from __future__ import annotations

import os
import time
from pathlib import Path

import cv2
import numpy as np
from scipy.interpolate import griddata


def save_cube_lut(lut: np.ndarray, path: str | os.PathLike[str]) -> None:
    """Save an RGB LUT array as a .cube file."""
    lut_size = _validate_lut(lut)
    destination = Path(path)
    lut_normalized = lut.astype(np.float32) / 255.0

    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Created by LUT Estimator\n")
        handle.write('TITLE "Estimated LUT"\n\n')
        handle.write(f"LUT_3D_SIZE {lut_size}\n\n")
        lines = [
            f"{r:.6f} {g:.6f} {b:.6f}"
            for r, g, b in lut_normalized.reshape(-1, 3)
        ]
        handle.write("\n".join(lines))
        handle.write("\n")


def apply_lut_trilinear(target_img_rgb: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Apply a LUT to an RGB image using trilinear interpolation."""
    _validate_image_array(target_img_rgb, "target_img_rgb")
    lut_size = _validate_lut(lut)

    target_float = target_img_rgb.astype(np.float32)
    scale = lut_size - 1
    coords = target_float * (scale / 255.0)

    x0 = np.floor(coords[:, :, 0]).astype(int)
    y0 = np.floor(coords[:, :, 1]).astype(int)
    z0 = np.floor(coords[:, :, 2]).astype(int)

    np.clip(x0, 0, lut_size - 2, out=x0)
    np.clip(y0, 0, lut_size - 2, out=y0)
    np.clip(z0, 0, lut_size - 2, out=z0)

    x1, y1, z1 = x0 + 1, y0 + 1, z0 + 1

    xd = (coords[:, :, 0] - x0)[..., np.newaxis]
    yd = (coords[:, :, 1] - y0)[..., np.newaxis]
    zd = (coords[:, :, 2] - z0)[..., np.newaxis]

    c000 = lut[x0, y0, z0]
    c100 = lut[x1, y0, z0]
    c010 = lut[x0, y1, z0]
    c001 = lut[x0, y0, z1]
    c110 = lut[x1, y1, z0]
    c101 = lut[x1, y0, z1]
    c011 = lut[x0, y1, z1]
    c111 = lut[x1, y1, z1]

    c00 = c000 * (1 - xd) + c100 * xd
    c01 = c001 * (1 - xd) + c101 * xd
    c10 = c010 * (1 - xd) + c110 * xd
    c11 = c011 * (1 - xd) + c111 * xd

    c0 = c00 * (1 - yd) + c10 * yd
    c1 = c01 * (1 - yd) + c11 * yd
    result = c0 * (1 - zd) + c1 * zd

    return np.clip(result, 0, 255).astype(np.uint8)


def estimate_lut(
    before_img_rgb: np.ndarray,
    after_img_rgb: np.ndarray,
    *,
    lut_size: int = 33,
    sample_rate: float = 0.01,
    blur_ksize: int = 5,
    seed: int | None = None,
) -> np.ndarray:
    """Estimate a LUT from a before/after RGB image pair."""
    _validate_image_array(before_img_rgb, "before_img_rgb")
    _validate_image_array(after_img_rgb, "after_img_rgb")
    _validate_parameters(lut_size=lut_size, sample_rate=sample_rate, blur_ksize=blur_ksize)

    before_work = before_img_rgb
    after_work = after_img_rgb

    if before_work.shape != after_work.shape:
        height = min(before_work.shape[0], after_work.shape[0])
        width = min(before_work.shape[1], after_work.shape[1])
        before_work = cv2.resize(before_work, (width, height), interpolation=cv2.INTER_AREA)
        after_work = cv2.resize(after_work, (width, height), interpolation=cv2.INTER_AREA)

    if blur_ksize > 0:
        before_work = cv2.GaussianBlur(before_work, (blur_ksize, blur_ksize), 0)
        after_work = cv2.GaussianBlur(after_work, (blur_ksize, blur_ksize), 0)

    before_pixels = before_work.reshape(-1, 3)
    after_pixels = after_work.reshape(-1, 3)

    num_pixels = len(before_pixels)
    requested_samples = max(2000, int(num_pixels * sample_rate))
    num_samples = min(num_pixels, requested_samples)

    rng = np.random.default_rng(seed)
    if num_samples == num_pixels:
        sampled_before = before_pixels
        sampled_after = after_pixels
    else:
        indices = rng.choice(num_pixels, num_samples, replace=False)
        sampled_before = before_pixels[indices]
        sampled_after = after_pixels[indices]

    grid_points = np.linspace(0, 255, lut_size)
    xi, yi, zi = np.meshgrid(grid_points, grid_points, grid_points, indexing="ij")
    grid_to_interpolate = np.vstack([xi.ravel(), yi.ravel(), zi.ravel()]).T

    estimated_lut_flat = griddata(
        points=sampled_before,
        values=sampled_after,
        xi=grid_to_interpolate,
        method="linear",
    )

    nan_indices = np.isnan(estimated_lut_flat).any(axis=1)
    if np.any(nan_indices):
        nearest_fill = griddata(
            points=sampled_before,
            values=sampled_after,
            xi=grid_to_interpolate[nan_indices],
            method="nearest",
        )
        estimated_lut_flat[nan_indices] = nearest_fill

    return np.clip(estimated_lut_flat, 0, 255).reshape((lut_size, lut_size, lut_size, 3))


def estimate_and_apply_lut(
    *,
    before_image_path: str | os.PathLike[str],
    after_image_path: str | os.PathLike[str],
    target_image_path: str | os.PathLike[str],
    output_image_path: str | os.PathLike[str] = "result_advanced.png",
    lut_size: int = 33,
    sample_rate: float = 0.01,
    blur_ksize: int = 5,
    save_cube: bool = True,
    seed: int | None = None,
) -> dict[str, str | float]:
    """Estimate a LUT from image files and apply it to a target image."""
    start_time = time.time()

    before_img_rgb = _read_image_rgb(before_image_path)
    after_img_rgb = _read_image_rgb(after_image_path)
    target_img_rgb = _read_image_rgb(target_image_path)

    estimated_lut = estimate_lut(
        before_img_rgb,
        after_img_rgb,
        lut_size=lut_size,
        sample_rate=sample_rate,
        blur_ksize=blur_ksize,
        seed=seed,
    )

    output_path = Path(output_image_path)
    result_img_rgb = apply_lut_trilinear(target_img_rgb, estimated_lut)
    result_img_bgr = cv2.cvtColor(result_img_rgb, cv2.COLOR_RGB2BGR)

    if not cv2.imwrite(str(output_path), result_img_bgr):
        raise OSError(f"Failed to write output image to '{output_path}'.")

    cube_path: Path | None = None
    if save_cube:
        cube_path = output_path.with_suffix(".cube")
        save_cube_lut(estimated_lut.astype(np.uint8), cube_path)

    return {
        "output_image": str(output_path),
        "cube_path": str(cube_path) if cube_path else "",
        "elapsed_seconds": time.time() - start_time,
    }


def _read_image_rgb(path: str | os.PathLike[str]) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Failed to read image '{path}'.")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _validate_image_array(image: np.ndarray, name: str) -> None:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"{name} must have shape (height, width, 3).")


def _validate_lut(lut: np.ndarray) -> int:
    if lut.ndim != 4 or lut.shape[-1] != 3:
        raise ValueError("lut must have shape (size, size, size, 3).")
    if lut.shape[0] < 2 or lut.shape[0] != lut.shape[1] or lut.shape[1] != lut.shape[2]:
        raise ValueError("lut must be cubic and at least size 2.")
    return int(lut.shape[0])


def _validate_parameters(*, lut_size: int, sample_rate: float, blur_ksize: int) -> None:
    if lut_size < 2:
        raise ValueError("lut_size must be >= 2.")
    if not 0 < sample_rate <= 1:
        raise ValueError("sample_rate must be within (0, 1].")
    if blur_ksize < 0 or blur_ksize % 2 == 0 and blur_ksize != 0:
        raise ValueError("blur_ksize must be 0 or a positive odd integer.")
