import os
import base64
import requests
import re
from PIL import Image
from dotenv import load_dotenv

# ==== 配置 ====
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL") or "https://api.openai-hk.com/v1"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
vision_model = os.getenv("OPENAI_MODEL_NAME") or "gpt-4-vision-preview"
text_model = "gpt-3.5-turbo-1106"
use_proxy = os.getenv("USE_PROXY", "False").lower() == "true"
proxy_url = os.getenv("PROXY_URL")
proxies = {"https": proxy_url} if use_proxy and proxy_url else None

report_dir = r"D:\DATA\outt"
file_prefix = "watch_2"   # ← 换成自己的文件前缀，比如"watch_2"

# ==== 图片压缩函数 ====
def compress_image(path, max_size=(1200, 1200), jpeg_quality=80):
    try:
        with Image.open(path) as img:
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.LANCZOS)
                img = img.convert("RGB")
                img.save(path, format="JPEG", quality=jpeg_quality)
    except Exception as e:
        print(f"❌ 压缩失败 {path}：{e}")

def img_to_base64(path):
    compress_image(path)
    with open(path, "rb") as img_f:
        return base64.b64encode(img_f.read()).decode("utf-8")

# ==== 结构化提取（同之前效果最好的版本）====
def extract_key_areas(report_text, top_k=10):
    pattern = r"\[区域 (\d+)\] 坐标: \(([\d, ]+)\)\s+总分: ([\d\.]+) \| ELA: ([\d\.]+) \| Noise: ([\d\.]+) \| FFT: ([\d\.]+)"
    results = re.findall(pattern, report_text)
    if not results:
        return "未检测到典型伪造区域。"
    area_list = []
    for item in results:
        idx, xywh, score, ela, noise, fft = item
        area_list.append({
            "编号": int(idx),
            "坐标": xywh,
            "总分": float(score),
            "ELA": float(ela),
            "Noise": float(noise),
            "FFT": float(fft),
        })
    area_list.sort(key=lambda x: -x["总分"])
    top_areas = area_list[:top_k]
    summary = ""
    for a in top_areas:
        summary += f"区域{a['编号']} | 坐标({a['坐标']}) | 总分{a['总分']:.2f} | ELA:{a['ELA']:.2f} | Noise:{a['Noise']:.2f} | FFT:{a['FFT']:.2f}\n"
    return summary.strip()

def gpt_summarize_key_areas(key_area_text, model=text_model):
    prompt = (
        "请根据以下检测区域数据，提炼主要伪造风险点、异常指标及聚集趋势，"
        "用简洁明了的中文输出总结（包含编号、坐标、得分、可疑区域分布、建议）。"
        "报告如下：\n" + key_area_text
    )
    payload = {
        "model": model,
        "max_tokens": 800,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "你是一名图像取证分析专家，擅长可疑区域总结与异常趋势分析。"},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=90
        )
        resp.raise_for_status()
        print("📑 文本摘要完成 ✅")
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ 文本摘要失败，使用原始结构代替：", e)
        return key_area_text

# ==== 批量主循环 ====
def process_batch_reports(report_dir, file_prefix, top_k=10):
    page = 1
    while True:
        tag = f"{file_prefix}_p{page}"
        report_path = os.path.join(report_dir, f"{tag}_report.txt")
        heatmap_path = os.path.join(report_dir, f"{tag}_heatmap.jpg")
        marked_path = os.path.join(report_dir, f"{tag}_marked.jpg")
        output_path = os.path.join(report_dir, f"{tag}_final_report.txt")

        if not os.path.exists(report_path):
            break  # 没有就停

        if not os.path.exists(heatmap_path) or not os.path.exists(marked_path):
            print(f"❌ 第{page}页缺图片，跳过")
            page += 1
            continue

        print(f"\n===== 正在处理第{page}页 =====")
        with open(report_path, "r", encoding="utf-8") as f:
            report_text = f.read()

        key_area_text = extract_key_areas(report_text, top_k=top_k)
        summarized_text = gpt_summarize_key_areas(key_area_text)

        heatmap_b64 = img_to_base64(heatmap_path)
        marked_b64 = img_to_base64(marked_path)

        payload = {
            "model": vision_model,
            "max_tokens": 1200,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名图像取证专家，擅长分析图像涂改和伪造行为。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"以下是伪造检测程序的核心摘要（数字结论+AI归纳），请结合热力图和标注图，综合分析并回答：\n"
                                    f"1. 是否存在伪造区域？\n"
                                    f"2. 高分数区域是否提示高度风险？\n"
                                    f"3. 是否建议人工复查？\n\n"
                                    f"【检测摘要如下】：\n{summarized_text}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{heatmap_b64}"}
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{marked_b64}"}
                        }
                    ]
                }
            ]
        }
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=120
            )
            response.raise_for_status()
            summary = response.json()["choices"][0]["message"]["content"]
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"✅ 第{page}页生成成功：{output_path}")
        except Exception as e:
            print(f"❌ 第{page}页生成失败：", e)
        page += 1

# ==== 执行批量处理 ====
if __name__ == "__main__":
    process_batch_reports(report_dir, file_prefix, top_k=10)
