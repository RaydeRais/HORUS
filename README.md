# HORUS
# PDF-Based Forgery Detection for Trade Contracts and Invoices

*Automated Batch Analysis System for Scanned Documents*

*Based on Customized OpenAI Vision API + Proprietary Local Algorithms*
**For Mainland China users. VPN required. Batch analysis of scanned PDFs with automated risk reporting.**

---

## 1. Project Overview

This toolkit enables **batch forgery and alteration detection** on scanned PDF documents, such as international trade contracts and invoices.
It combines pixel-level anomaly detection algorithms with OpenAI’s state-of-the-art multimodal models, providing **one-click risk reports and visual annotations for each page**. Ideal applications include:

* Customs inspection and compliance audits
* Enterprise-level due diligence
* Financial document verification
* External contract archiving and review

---

## 2. Core Features

* **Batch PDF Processing**: Automatically analyzes every page of each PDF, generating a textual risk report (TXT) plus two annotated heatmaps (JPG) per page.
* **Priority Region Extraction**: Pinpoints and structures the top 10 regions on each page with the highest forgery risk.
* **AI-Powered Summarization**: Utilizes GPT-3.5-turbo/4 to aggregate and summarize risk indicators in high-risk regions.
* **Vision Model Final Judgment**: Merges image analysis with AI summaries to deliver a “final expert report” in a professional style.
* **Automatic Image Compression**: Downscales large JPGs to optimize performance and minimize interruptions.
* **Mainland-Friendly API/Proxy Support**: Ships with a `.env` configuration for easy integration with VPNs and customized OpenAI API providers (tested with `openai-hk` and others).

---

## 3. Project Structure

```
|-- ppdf_check_pro7_TRUE.py       # Page-level PDF forgery risk detection (generates TXT + 2 JPGs)
|-- ALYSIS_PRO_9_TRUE.PY          # Batch AI summarization and final reporting (calls OpenAI Vision)
|-- .env                          # API and proxy configuration (customizable)
|-- /outt                         # Output directory (all results auto-saved here)
|-- /invoice                      # Input PDF directory
```

---

## 4. Getting Started

### 1. Environment Setup

* **Python 3.8+ required**
* Recommended libraries:
  `pip install pillow requests python-dotenv pdf2image opencv-python`
* Obtain a working “customized API KEY” and a VPN (prefer Singapore or Hong Kong nodes; avoid US West, Japan, or Korea).

### 2. Configure `.env`

(**Do not disclose!** API keys and proxy details must remain confidential.)

```
OPENAI_API_KEY=hk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai-hk.com/v1
OPENAI_MODEL_NAME=gpt-4-vision-preview
USE_PROXY=True
PROXY_URL=http://127.0.0.1:33210
```

### 3. Workflow

#### Step 1: PDF Preprocessing & Feature Extraction

(Generates TXT + 2 JPGs per page)

```bash
python ppdf_check_pro7_TRUE.py
```

* Input: Place your scanned PDF files in the `/invoice` directory and adjust path settings as needed.
* Output: For each page, outputs `{base}_p{n}_report.txt`, `{base}_p{n}_heatmap.jpg`, and `{base}_p{n}_marked.jpg` to `/outt`.

#### Step 2: Batch AI Analysis & Final Reporting

```bash
python ALYSIS_PRO_9_TRUE.PY
```

* Automatically traverses all outputs in `/outt`, synthesizing high-quality “final reports” as `{base}_p{n}_final_report.txt`.
* Process: Local algorithms pre-select regions → GPT-3/4 aggregates findings → Vision model delivers AI-based expert judgment.
* **Note:** API instability or proxy issues may cause failures. If so, retry or switch VPN nodes.

---

## 5. Output File Guide

* `*_report.txt`: Raw detection details for each suspected region (region ID, coordinates, risk score, metrics)
* `*_heatmap.jpg`: Heatmap visualizing tampering/anomaly likelihood (darker = higher risk)
* `*_marked.jpg`: Visualization with bounding boxes highlighting high-risk areas
* `*_final_report.txt`: Multimodal AI expert report—suitable for official documentation or internal review

---

## 6. Frequently Asked Questions

1. **Unable to connect to API / timeout?**
   Try switching VPN nodes (Singapore/Hong Kong recommended) or restarting the customized API service.

2. **Image too large / processing error?**
   System auto-compresses images; JPGs up to 3MB tested stable. For very large PDFs, consider splitting or lowering DPI.

3. **No suspicious region in report?**
   This may indicate a clean page or that the detection threshold is too high/low. Adjust `threshold_score` as needed.

4. **Token usage too high?**
   GPT-3.5-turbo is generally sufficient. For large batches, avoid using GPT-4 to control costs.

---

## 7. Security Notice

* All configurations (especially API keys and proxy) are for internal use only. **Do not share externally.**
* This tool is intended for research and technical exploration only; formal forensic work should always involve human review.

---

For special requests or bug reports, feel free to @ the developer in this chat at any time.

---

Let me know if you need further details, a tailored README, or an English-language code sample!
