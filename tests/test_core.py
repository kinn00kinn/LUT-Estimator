from pathlib import Path

import numpy as np

from lut_estimator.core import apply_lut_trilinear, estimate_lut, save_cube_lut


def test_apply_lut_trilinear_with_identity_lut() -> None:
    lut = np.zeros((2, 2, 2, 3), dtype=np.float32)
    for r in range(2):
        for g in range(2):
            for b in range(2):
                lut[r, g, b] = [r * 255, g * 255, b * 255]

    image = np.array(
        [
            [[0, 0, 0], [255, 255, 255]],
            [[128, 64, 32], [32, 200, 128]],
        ],
        dtype=np.uint8,
    )

    result = apply_lut_trilinear(image, lut)
    assert np.allclose(result, image, atol=1)


def test_estimate_lut_identity_mapping_preserves_endpoints() -> None:
    values = np.array([0, 128, 255], dtype=np.uint8)
    rr, gg, bb = np.meshgrid(values, values, values, indexing="ij")
    before = np.stack([rr, gg, bb], axis=-1).reshape(3, 9, 3)
    after = before.copy()

    lut = estimate_lut(
        before,
        after,
        lut_size=3,
        sample_rate=1.0,
        blur_ksize=0,
        seed=123,
    )

    assert np.allclose(lut[0, 0, 0], [0, 0, 0], atol=1)
    assert np.allclose(lut[-1, -1, -1], [255, 255, 255], atol=1)


def test_save_cube_lut_writes_expected_header(tmp_path: Path) -> None:
    lut = np.zeros((2, 2, 2, 3), dtype=np.uint8)
    output = tmp_path / "sample.cube"

    save_cube_lut(lut, output)

    content = output.read_text(encoding="utf-8")
    assert 'TITLE "Estimated LUT"' in content
    assert "LUT_3D_SIZE 2" in content
