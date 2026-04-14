# LUT Estimator

英語版 README を既定としつつ、日本語の概要をこちらに分離しています。

画像の before / after ペアから 3D LUT を推定し、そのルックを別の画像へ適用する Python ツールです。ライブラリ API と CLI の両方を用意しているため、スクリプト利用にも OSS 利用にも載せやすい構成にしています。

## 主な特徴

- 画像ペアから 3D LUT を推定
- LUT 適用時にトライリニア補間を使用
- 推定前のガウシアンブラーに対応
- `.cube` 形式で LUT を出力
- Python API と CLI の両方を提供

## インストール

```bash
python -m pip install -e .[dev]
```

実行だけでよければ:

```bash
python -m pip install -e .
```

## CLI の使い方

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

## 開発

```bash
pytest
pre-commit install
```

詳細は英語版 [README.md](README.md) を参照してください。
