# QQS

QQS is a small local web app for entering invoice request information and generating a Japanese PDF invoice with one button.

## Features

- Browser-based invoice request form
- One-click PDF download
- Built-in ニワノテ issuer and bank details
- Japanese PDF output using ReportLab CJK fonts

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:8765
```

## Run on GitHub Codespaces

After this project is pushed to GitHub:

1. Open the repository on GitHub.
2. Click `Code` -> `Codespaces` -> `Create codespace on main`.
3. Wait until dependencies install automatically.
4. Run:

```bash
python app.py
```

Codespaces will forward port `8765` and open the QQS invoice form in the browser.

GitHub Pages is not suitable for this app as-is because QQS uses a Python backend to generate the PDF. Codespaces keeps the one-click PDF download behavior.

## Test

```bash
python -m compileall app.py
python tests/smoke_pdf.py
```

## Default Issuer

- 事業名: ニワノテ
- 氏名: 南 理奈
- 振込先: 住信SBIネット銀行 レモン支店 普通 9501239
- 口座名義: ミナミ リナ

ニワノテは適格請求書発行事業者登録番号を記載しない設定です。
