import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageChops, ImageEnhance

# ========== 配置 ==========
pdf_path = r"D:\DATA\invoice\blanket.pdf"
output_dir = r"D:\DATA\outt"
dpi = 300
threshold_score = 0.6
save_patch = False  # ← 如需保存图块区域，设为 True

os.makedirs(output_dir, exist_ok=True)

# ========== 功能函数 ==========
def error_level_analysis(img, quality=90):
    temp_file = "temp_ela.jpg"
    img.save(temp_file, 'JPEG', quality=quality)
    ela_img = Image.open(temp_file)
    diff = ImageChops.difference(img, ela_img)
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff if max_diff != 0 else 1
    diff = ImageEnhance.Brightness(diff).enhance(scale)
    return np.array(diff)

def noise_variance_map(gray):
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    noise = cv2.absdiff(gray, blur)
    return cv2.GaussianBlur(noise, (3, 3), 0)

def fft_anomaly(gray):
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1)
    return cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# ========== 主流程 ==========
images = convert_from_path(pdf_path, dpi=dpi)
base_name = os.path.splitext(os.path.basename(pdf_path))[0]

for i, pil_img in enumerate(images, start=1):
    print(f"[·] 分析第{i}页...")
    img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    ela = cv2.cvtColor(error_level_analysis(pil_img), cv2.COLOR_RGB2GRAY)
    noise = noise_variance_map(gray)
    fft_map = fft_anomaly(gray)

    ela_norm = cv2.normalize(ela, None, 0, 1.0, cv2.NORM_MINMAX)
    noise_norm = cv2.normalize(noise, None, 0, 1.0, cv2.NORM_MINMAX)
    fft_norm = cv2.normalize(fft_map, None, 0, 1.0, cv2.NORM_MINMAX)

    score_map = (ela_norm + noise_norm + fft_norm) / 3.0
    binary_mask = (score_map > threshold_score).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    marked_img = img_cv.copy()
    report_lines = []

    for idx, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        patch_score = float(np.mean(score_map[y:y+h, x:x+w]))
        if patch_score < threshold_score:
            continue

        ela_s = float(np.mean(ela_norm[y:y+h, x:x+w]))
        noise_s = float(np.mean(noise_norm[y:y+h, x:x+w]))
        fft_s = float(np.mean(fft_norm[y:y+h, x:x+w]))

        cv2.rectangle(marked_img, (x, y), (x + w, y + h), (0, 0, 255), 2)

        if save_patch:
            patch_img = img_cv[y:y+h, x:x+w]
            patch_path = os.path.join(output_dir, f"{base_name}_p{i}_patch{idx+1}.jpg")
            cv2.imwrite(patch_path, patch_img)

        report_lines.append(
            f"[区域 {idx+1}] 坐标: ({x},{y},{w},{h})"
            f"\n  总分: {patch_score:.2f} | ELA: {ela_s:.2f} | Noise: {noise_s:.2f} | FFT: {fft_s:.2f}\n"
        )

    heatmap_color = cv2.applyColorMap((score_map * 255).astype(np.uint8), cv2.COLORMAP_JET)

    marked_path = os.path.join(output_dir, f"{base_name}_p{i}_marked.jpg")
    heatmap_path = os.path.join(output_dir, f"{base_name}_p{i}_heatmap.jpg")
    report_path = os.path.join(output_dir, f"{base_name}_p{i}_report.txt")

    cv2.imwrite(marked_path, marked_img)
    cv2.imwrite(heatmap_path, heatmap_color)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"==== 涂改痕迹检测报告 v3.0 ====\nPDF文件: {pdf_path}\n页码: 第{i}页\n\n")
        if report_lines:
            f.write("\n".join(report_lines))
        else:
            f.write("未检测到明显可疑区域。\n")

    print(f"[✅] 第{i}页完成，结果保存在：{output_dir}")
