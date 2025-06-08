import cv2
import numpy as np
from scipy.interpolate import griddata
import time
import os

def _save_cube_lut(lut, path, lut_size):
    """推定したLUTを.cubeファイル形式で保存するヘルパー関数。"""
    try:
        lut_normalized = lut.astype(np.float32) / 255.0
        with open(path, 'w') as f:
            f.write(f'# Created by Advanced Python LUT Estimator\n')
            f.write(f'TITLE "Estimated LUT"\n\n')
            f.write(f'LUT_3D_SIZE {lut_size}\n\n')
            
            # NumPyの高速な操作でテキストを生成してから書き出す
            lines = [f'{r:.6f} {g:.6f} {b:.6f}' for r, g, b in lut_normalized.reshape(-1, 3)]
            f.write('\n'.join(lines))
            f.write('\n') # ファイル末尾に改行
        print(f"✅ LUTを '{path}' に保存しました。")
    except Exception as e:
        print(f"❌ .cubeファイルの保存中にエラーが発生しました: {e}")

def _apply_lut_trilinear(target_img_rgb, lut):
    """
    トライリニア補間を用いてLUTを高速に適用する関数。
    これがバンディングを抑制する鍵となります。
    """
    target_float = target_img_rgb.astype(np.float32)
    lut_size = lut.shape[0]
    
    # ピクセル値をLUTの浮動小数点インデックスに変換
    # (例: 255 -> 32.0 for lut_size=33)
    scale = lut_size - 1
    coords = target_float * (scale / 255.0)

    # 補間に使う8つの近傍格子点のインデックスを計算
    x0 = np.floor(coords[:, :, 0]).astype(int)
    y0 = np.floor(coords[:, :, 1]).astype(int)
    z0 = np.floor(coords[:, :, 2]).astype(int)
    
    # 範囲外のインデックスをクリップしてエラーを防ぐ
    np.clip(x0, 0, lut_size - 2, out=x0)
    np.clip(y0, 0, lut_size - 2, out=y0)
    np.clip(z0, 0, lut_size - 2, out=z0)
    
    x1, y1, z1 = x0 + 1, y0 + 1, z0 + 1

    # 格子点間の距離（重み）を計算
    xd = coords[:, :, 0] - x0
    yd = coords[:, :, 1] - y0
    zd = coords[:, :, 2] - z0
    
    # (H, W, 1) の形状にしないとブロードキャストがうまく機能しない
    xd, yd, zd = xd[..., np.newaxis], yd[..., np.newaxis], zd[..., np.newaxis]

    # 8つの近傍格子点の値を取得
    c000 = lut[x0, y0, z0]
    c100 = lut[x1, y0, z0]
    c010 = lut[x0, y1, z0]
    c001 = lut[x0, y0, z1]
    c110 = lut[x1, y1, z0]
    c101 = lut[x1, y0, z1]
    c011 = lut[x0, y1, z1]
    c111 = lut[x1, y1, z1]

    # トライリニア補間をNumPyのベクトル演算で一気に実行
    c00 = c000 * (1 - xd) + c100 * xd
    c01 = c001 * (1 - xd) + c101 * xd
    c10 = c010 * (1 - xd) + c110 * xd
    c11 = c011 * (1 - xd) + c111 * xd

    c0 = c00 * (1 - yd) + c10 * yd
    c1 = c01 * (1 - yd) + c11 * yd

    c = c0 * (1 - zd) + c1 * zd
    
    return np.clip(c, 0, 255).astype(np.uint8)


def estimate_and_apply_lut_advanced(
    before_image_path: str,
    after_image_path: str,
    target_image_path: str,
    output_image_path: str = 'result_advanced.png',
    lut_size: int = 33,
    sample_rate: float = 0.01,
    blur_ksize: int = 5,
    save_cube: bool = True
):
    """
    改良版：LUTを推定し、ターゲット画像に適用するメイン関数。
    """
    start_time = time.time()

    # --- 1. 画像の読み込みと前処理 ---
    print("1/5: 画像を読み込んでいます...")
    before_img = cv2.imread(before_image_path)
    after_img = cv2.imread(after_image_path)
    target_img = cv2.imread(target_image_path)

    if before_img is None or after_img is None or target_img is None:
        print("❌ エラー: 画像ファイルの読み込みに失敗しました。パスを確認してください。")
        return

    before_img_rgb = cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB)
    after_img_rgb = cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB)
    target_img_rgb = cv2.cvtColor(target_img, cv2.COLOR_BGR2RGB)

    if before_img_rgb.shape != after_img_rgb.shape:
        h = min(before_img_rgb.shape[0], after_img_rgb.shape[0])
        w = min(before_img_rgb.shape[1], after_img_rgb.shape[1])
        before_img_rgb = cv2.resize(before_img_rgb, (w, h), interpolation=cv2.INTER_AREA)
        after_img_rgb = cv2.resize(after_img_rgb, (w, h), interpolation=cv2.INTER_AREA)

    # 【改良点】ノイズ低減のため、推定用の画像にガウシアンブラーを適用
    if blur_ksize > 0:
        print(f"   - 推定精度向上のため、入力画像に平滑化処理 (GaussianBlur: ksize={blur_ksize}) を適用します。")
        before_img_rgb = cv2.GaussianBlur(before_img_rgb, (blur_ksize, blur_ksize), 0)
        after_img_rgb = cv2.GaussianBlur(after_img_rgb, (blur_ksize, blur_ksize), 0)

    # --- 2. 色の変化をサンプリング ---
    print("2/5: 色の変化をピクセルからサンプリングしています...")
    before_pixels = before_img_rgb.reshape(-1, 3)
    after_pixels = after_img_rgb.reshape(-1, 3)
    
    num_pixels = len(before_pixels)
    num_samples = max(2000, int(num_pixels * sample_rate))
    
    indices = np.random.choice(num_pixels, num_samples, replace=False)
    sampled_before = before_pixels[indices]
    sampled_after = after_pixels[indices]

    # --- 3. 3D LUTの推定 (堅牢な2段階補間) ---
    print(f"3/5: {lut_size}x{lut_size}x{lut_size}の3D LUTを堅牢な手法で推定中...")
    
    grid_points = np.linspace(0, 255, lut_size)
    xi, yi, zi = np.meshgrid(grid_points, grid_points, grid_points, indexing='ij')
    grid_to_interpolate = np.vstack([xi.ravel(), yi.ravel(), zi.ravel()]).T

    # 【改良点】1段階目: 線形補間
    estimated_lut_flat = griddata(
        points=sampled_before, values=sampled_after, xi=grid_to_interpolate, method='linear'
    )
    
    # 【改良点】2段階目: 線形補間で埋まらなかったNaNの部分を最近傍法で埋める
    nan_indices = np.isnan(estimated_lut_flat).any(axis=1)
    if np.any(nan_indices):
        print("   - 未知の色領域を最近傍法で補完しています...")
        nearest_fill = griddata(
            points=sampled_before, values=sampled_after, xi=grid_to_interpolate[nan_indices], method='nearest'
        )
        estimated_lut_flat[nan_indices] = nearest_fill

    estimated_lut = np.clip(estimated_lut_flat, 0, 255).reshape((lut_size, lut_size, lut_size, 3))

    if save_cube:
        cube_filename = os.path.splitext(output_image_path)[0] + '.cube'
        _save_cube_lut(estimated_lut.astype(np.uint8), cube_filename, lut_size)

    # --- 4. ターゲット画像へのLUT適用 (トライリニア補間) ---
    print("4/5: 推定したLUTをターゲット画像に高精度適用しています...")
    result_img_rgb = _apply_lut_trilinear(target_img_rgb, estimated_lut)

    # --- 5. 結果の保存 ---
    print("5/5: 結果をファイルに保存しています...")
    result_img_bgr = cv2.cvtColor(result_img_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_image_path, result_img_bgr)

    end_time = time.time()
    print(f"✨ 処理が完了しました！ ({end_time - start_time:.2f}秒)")
    print(f"   - 結果画像: '{output_image_path}'")

# --- ここからプログラムを実行 ---
if __name__ == '__main__':
    # 💥💥💥 あなたの画像ファイルパスに書き換えてください 💥💥💥
    BEFORE_IMAGE = 'img/base.JPG' 
    AFTER_IMAGE = 'img/apply_lut.JPG'  
    TARGET_IMAGE = 'img/base.JPG'
    
    OUTPUT_IMAGE = 'apply_estimated_lut.jpg'
    
    # パス存在チェック
    if 'path/to/your' in BEFORE_IMAGE:
        print("="*60)
        print("⚠️ エラー: プログラム内の画像パスが設定されていません。")
        print("`BEFORE_IMAGE`, `AFTER_IMAGE`, `TARGET_IMAGE` を書き換えてください。")
        print("="*60)
    else:
        estimate_and_apply_lut_advanced(
            before_image_path=BEFORE_IMAGE,
            after_image_path=AFTER_IMAGE,
            target_image_path=TARGET_IMAGE,
            output_image_path=OUTPUT_IMAGE,
            lut_size=33,        # 33が標準的。17にすると高速、65にすると高精度（ただし推定に時間がかかる）
            sample_rate=0.02,   # サンプリング率。少し多めに設定 (2%)。
            blur_ksize=0,       # ノイズ低減のためのブラー強度。0でオフ。奇数を指定。
            save_cube=True
        )