# 高精度 LUT 推定・適用ツール (Advanced LUT Estimator)

![GitHub](https://img.shields.io/github/license/mashape/apistatus.svg) ![Python](https://img.shields.io/badge/python-3.x-blue.svg)

LUT 適用前後の画像ペアから 3D カラーコレクション情報（3D LUT）を推定し、別の画像に高品質に適用するための Python スクリプトです。

ノイズやトーンジャンプ（バンディング）を抑制するための高度な画像処理技術を実装しており、既存のプリセットの再現や、好みのルックを他の写真・映像に適用する際に役立ちます。

<p align="center">
  <img src="img/base.JPG" width="400" alt="図1 LUT適用前">
</p>


<p align="center"><b>図 1: LUT 適用前</b></p>

<p align="center">
  <img src="img/apply_lut.JPG" width="400" alt="図2 あらかじめ用意したLUTを適用">
</p>

<p align="center"><b>図2: あらかじめ用意したLUTを適用</b></p>

<p align="center">
  <img src="apply_estimated_lut.jpg" width="400" alt="図3 推定したLUTを適用 (元の画像)">
</p>


<p align="center"><b>図 3: 推定した LUT を適用 (元の画像)</b></p>

## 主な特徴

- **高精度な LUT 推定**: 適用前後の画像から、`SciPy`を用いた堅牢な 2 段階補間（線形補間 + 最近傍法）により、色変換ルールを正確に推定します。
- **滑らかな色再現**: LUT 適用時に**トライリニア補間**を実装。色の階調が滑らかに再現され、トーンジャンプ（バンディング）を劇的に抑制します。
- **ノイズ抑制**: 推定前に入力画像を平滑化（ガウシアンブラー）するオプションを備え、元画像に含まれるノイズの影響を受けにくい、より安定した推定が可能です。
- **高速処理**: `NumPy`によるベクトル化演算を全面的に採用し、ピクセル単位の低速なループ処理を回避。大量のピクセルデータを高速に処理します。
- **汎用的な出力**: 推定した LUT は、業界標準の`.cube`形式でエクスポート可能。Adobe Photoshop, DaVinci Resolve, Lightroom (プラグイン経由)など、多くのソフトウェアで再利用できます。

## 動作要件

- Python 3.6 以上
- ライブラリ:
  - NumPy
  - OpenCV-Python
  - SciPy

## インストール

1.  このリポジトリをクローンするか、Python スクリプト (`lut_estimator.py` など) をダウンロードします。

2.  ターミナルまたはコマンドプロンプトを開き、必要なライブラリをインストールします。

    ```bash
    pip install numpy opencv-python scipy
    ```

## 使い方

### 1. ファイルの準備

以下の 3 つの画像ファイルを用意します。

- **適用前の画像**: `before.jpg` など、元の状態の画像。
- **適用後の画像**: `after.jpg` など、目的の LUT やカラーコレクションが適用された見本となる画像。
- **ターゲット画像**: `target.jpg` など、推定した LUT を新たに適用したい画像。

### 2. プログラムの編集

スクリプトファイル（例: `lut_estimator.py`）を開き、末尾の `if __name__ == '__main__':` ブロック内にあるファイルパスを、あなたが用意した画像のものに書き換えます。

```python
# --- ここからプログラムを実行 ---
if __name__ == '__main__':
    # 💥💥💥 あなたの画像ファイルパスに書き換えてください 💥💥💥
    BEFORE_IMAGE = 'path/to/your/before_image.jpg'
    AFTER_IMAGE = 'path/to/your/after_image.jpg'
    TARGET_IMAGE = 'path/to/your/target_image.jpg'

    # --- 出力ファイル名 ---
    OUTPUT_IMAGE = 'result_advanced_output.jpg'

    # パラメータを調整（任意）
    estimate_and_apply_lut_advanced(
        before_image_path=BEFORE_IMAGE,
        after_image_path=AFTER_IMAGE,
        target_image_path=TARGET_IMAGE,
        output_image_path=OUTPUT_IMAGE,
        # ... その他のパラメータ
    )
```

### 3. 実行

ターミナルまたはコマンドプロンプトで、スクリプトを実行します。

```bash
python lut_estimator.py
```

処理が完了すると、指定した出力パスに結果画像と**.cube ファイル**が保存されます。

## パラメータの調整

スクリプト内の以下のパラメータを調整することで、結果の品質と処理速度をコントロールできます。

- lut_size (int): 生成する 3D LUT のグリッドサイズ。値が大きいほど精度が向上しますが、推定にかかる時間が増加します。
  - 17: 高速だが、色の階調が粗くなる可能性。
  - 33: 速度と精度のバランスが良い標準的な値。
  - 65: 高品質だが、推定に時間がかかる。
- sample_rate (float): 色変換の推定に使用する元画像のピクセル割合。0.01 は 1%を意味します。画像の色の種類が豊富な場合は、0.05 (5%) などに増やすと精度が向上することがあります。
- blur_ksize (int): 推定前に行う平滑化（ガウシアンブラー）のカーネルサイズ。3, 5, 7 などの奇数を指定します。ノイズが多い画像で有効です。0 に設定すると平滑化を無効化します。

## 処理の仕組み

このツールは、高品質な結果を得るために以下の数理モデルに基づいています。

### LUT 推定プロセス

1. 平滑化: 入力された before/after 画像にガウシアンブラーを適用し、センサーノイズや圧縮アーティファクトの影響を低減します。
2. サンプリング: 画像からランダムにピクセルを抽出し、「入力 RGB 値」と「出力 RGB 値」の対応ペアを大量に収集します。
3. 2 段階補間:
   1. 線形補間: まず、サンプルデータが存在する色空間領域を scipy.griddata の線形（linear）補間で高精度に推定します。
   2. 最近傍法: 線形補間だけではカバーできない未知の領域（サンプルデータから遠い色）を、最も近いサンプルデータの色で埋める最近傍（nearest）補間を行います。これにより、推定の安定性と堅牢性を両立しています。

### LUT 適用プロセス

トライリニア補間 (Trilinear Interpolation): 結果画像の色を決定する際、単純に最も近い LUT 格子点を参照するのではなく、そのピクセルの色が LUT の色空間内で囲まれる立方体の 8 つの格子点を参照します。そして、そのピクセルの座標に応じた重み付け平均を計算することで、滑らかで連続的な色の変化を実現し、バンディングを防ぎます。これはコンピュータグラフィックスにおける標準的なテクスチャマッピング技術です。

## ライセンス

このプロジェクトは MIT License の下で公開されています。
