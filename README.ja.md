# LUT Estimator

英語版 README を既定としつつ、日本語の概要をこちらに分離しています。

画像の before / after ペアから 3D LUT を推定し、そのルックを別の画像へ適用する Python ツールです。PyPI に公開されており、CLI と Python API の両方を使えます。

## 主な特徴

- 画像ペアから 3D LUT を推定
- LUT 適用時にトライリニア補間を使用
- 推定前のガウシアンブラーに対応
- `.cube` 形式で LUT を出力
- Python API と CLI の両方を提供

## インストール

PyPI から入れる場合:

```bash
python -m pip install lut-estimator
```

インストール後は:

- `lut-estimator` コマンドを実行できる
- Python から `lut_estimator` を import できる

開発用にソースから入れる場合:

```bash
python -m pip install -e .[dev]
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

ヘルプ表示:

```bash
lut-estimator --help
```

## 開発

```bash
pytest
pre-commit install
```

詳細は英語版 [README.md](README.md) を参照してください。
