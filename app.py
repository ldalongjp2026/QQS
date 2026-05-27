from __future__ import annotations

import io
import json
import re
from datetime import date
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
HOST = "127.0.0.1"
PORT = 8765

ISSUER = {
    "business": "ニワノテ",
    "owner": "南 理奈",
    "address": "奈良市油阪地方町1-1-808",
    "phone": "080-6125-1688",
    "bank": "住信SBIネット銀行",
    "branch": "レモン支店",
    "account_type": "普通",
    "account_no": "9501239",
    "account_name": "ミナミ リナ",
}


def money(value: int) -> str:
    return f"{value:,}円"


def parse_amount(raw: str) -> int:
    cleaned = re.sub(r"[^\d]", "", raw or "")
    return int(cleaned) if cleaned else 0


def safe_filename(text: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "_", text.strip())
    return cleaned[:40] or "請求書"


def field(data: dict, key: str, default: str = "") -> str:
    value = str(data.get(key, default)).strip()
    return value if value else default


def draw_right(c: canvas.Canvas, text: str, x: float, y: float, size: float = 10) -> None:
    c.setFont("HeiseiKakuGo-W5", size)
    c.drawRightString(x, y, text)


def build_pdf(data: dict) -> bytes:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    recipient = field(data, "recipient", "宛先未入力")
    subject = field(data, "subject", "庭の手入れ 人工費")
    item = field(data, "item", subject)
    quantity = field(data, "quantity", "1式")
    issue_date = field(data, "issueDate", date.today().strftime("%Y年%-m月%-d日"))
    due_date = field(data, "dueDate", "要確認")
    invoice_no = field(data, "invoiceNo", "なし")
    tax_status = field(data, "taxStatus", "要確認")
    amount = parse_amount(field(data, "amount", "0"))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 22 * mm
    right = width - 22 * mm
    top = height - 22 * mm

    blue = colors.HexColor("#1F4E79")
    pale_blue = colors.HexColor("#EAF2F8")
    line = colors.HexColor("#D9E2EA")
    text_gray = colors.HexColor("#555555")

    c.setTitle(f"請求書_{recipient}_{issue_date}")

    c.setFillColor(blue)
    c.rect(0, height - 34 * mm, width, 34 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("HeiseiKakuGo-W5", 24)
    c.drawString(left, height - 23 * mm, "請求書")
    c.setFont("HeiseiKakuGo-W5", 9)
    c.drawRightString(right, height - 16 * mm, ISSUER["business"])
    c.drawRightString(right, height - 22 * mm, ISSUER["owner"])
    c.drawRightString(right, height - 28 * mm, ISSUER["address"])

    y = top - 32 * mm
    c.setFillColor(colors.black)
    c.setFont("HeiseiKakuGo-W5", 13)
    c.drawString(left, y, f"{recipient} 御中")
    c.setStrokeColor(line)
    c.line(left, y - 4 * mm, left + 78 * mm, y - 4 * mm)
    draw_right(c, f"請求日: {issue_date}", right, y + 1 * mm)
    draw_right(c, f"請求番号: {invoice_no}", right, y - 6 * mm)

    y -= 26 * mm
    c.setFillColor(pale_blue)
    c.roundRect(left, y - 28 * mm, right - left, 28 * mm, 2 * mm, stroke=0, fill=1)
    c.setFillColor(blue)
    c.setFont("HeiseiKakuGo-W5", 10)
    c.drawString(left + 8 * mm, y - 10 * mm, "ご請求金額")
    c.setFont("HeiseiKakuGo-W5", 24)
    c.drawString(left + 8 * mm, y - 22 * mm, money(amount))
    c.setFont("HeiseiKakuGo-W5", 9)
    c.setFillColor(text_gray)
    c.drawRightString(right - 8 * mm, y - 12 * mm, f"税区分: {tax_status}")
    c.drawRightString(right - 8 * mm, y - 21 * mm, f"お支払期限: {due_date}")

    y -= 43 * mm
    c.setFont("HeiseiKakuGo-W5", 9.5)
    c.setFillColor(colors.HexColor("#444444"))
    c.drawString(left, y, "件名")
    c.setFillColor(colors.black)
    c.setFont("HeiseiKakuGo-W5", 10.5)
    c.drawString(left + 32 * mm, y, subject)
    y -= 14 * mm

    table_w = right - left
    col_w = [78 * mm, 22 * mm, 30 * mm, table_w - 130 * mm]
    row_h = 11 * mm

    c.setFillColor(blue)
    c.rect(left, y - row_h, table_w, row_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("HeiseiKakuGo-W5", 9.5)
    headers = ["品目", "数量", "単価", "金額"]
    x = left
    for i, header in enumerate(headers):
        c.drawCentredString(x + col_w[i] / 2, y - 7 * mm, header)
        x += col_w[i]

    y -= row_h
    c.setStrokeColor(line)
    c.rect(left, y - row_h, table_w, row_h, stroke=1, fill=0)
    x = left
    for width_part in col_w[:-1]:
        x += width_part
        c.line(x, y, x, y - row_h)

    c.setFillColor(colors.black)
    c.setFont("HeiseiKakuGo-W5", 9.5)
    c.drawString(left + 4 * mm, y - 7 * mm, item)
    c.drawCentredString(left + col_w[0] + col_w[1] / 2, y - 7 * mm, quantity)
    c.drawRightString(left + col_w[0] + col_w[1] + col_w[2] - 4 * mm, y - 7 * mm, money(amount))
    c.drawRightString(right - 4 * mm, y - 7 * mm, money(amount))

    y -= row_h + 12 * mm
    total_x = right - 72 * mm
    label_w = 34 * mm
    value_w = 38 * mm
    total_rows = [("小計", money(amount)), ("消費税", tax_status), ("合計", money(amount))]
    for idx, (label, value) in enumerate(total_rows):
        c.setFillColor(pale_blue if idx == 2 else colors.white)
        c.rect(total_x, y - row_h, label_w + value_w, row_h, stroke=0, fill=1)
        c.setStrokeColor(line)
        c.rect(total_x, y - row_h, label_w + value_w, row_h, stroke=1, fill=0)
        c.line(total_x + label_w, y, total_x + label_w, y - row_h)
        c.setFillColor(colors.black)
        c.setFont("HeiseiKakuGo-W5", 9.5 if idx < 2 else 10.5)
        c.drawString(total_x + 4 * mm, y - 7 * mm, label)
        c.drawRightString(total_x + label_w + value_w - 4 * mm, y - 7 * mm, value)
        y -= row_h

    y -= 14 * mm
    box_h = 45 * mm
    gap = 12 * mm
    box_w = (right - left - gap) / 2
    bank_x = left
    issuer_x = left + box_w + gap
    box_y = y - box_h
    for box_x in (bank_x, issuer_x):
        c.setFillColor(colors.white)
        c.roundRect(box_x, box_y, box_w, box_h, 1.5 * mm, stroke=1, fill=0)

    c.setFillColor(blue)
    c.setFont("HeiseiKakuGo-W5", 12)
    c.drawString(bank_x + 5 * mm, y - 8 * mm, "お振込先")
    c.drawString(issuer_x + 5 * mm, y - 8 * mm, "請求者")

    c.setFillColor(colors.black)
    c.setFont("HeiseiKakuGo-W5", 9.5)
    for line_text in [
        f'{ISSUER["bank"]}　{ISSUER["branch"]}',
        f'{ISSUER["account_type"]}　{ISSUER["account_no"]}',
        f'口座名義: {ISSUER["account_name"]}',
    ]:
        y -= 7 * mm
        c.drawString(bank_x + 5 * mm, y - 11 * mm, line_text)

    y2 = box_y + box_h
    for line_text in [ISSUER["business"], ISSUER["owner"], ISSUER["address"], ISSUER["phone"]]:
        y2 -= 7 * mm
        c.drawString(issuer_x + 5 * mm, y2 - 11 * mm, line_text)

    y = box_y - 8 * mm
    c.setFillColor(text_gray)
    c.setFont("HeiseiMin-W3", 8.5)
    c.drawString(left, y, "恐れ入りますが、振込手数料は貴社にてご負担くださいますようお願いいたします。")
    y -= 6 * mm
    c.drawString(left, y, "※ ニワノテは適格請求書発行事業者登録番号を記載していません。")

    c.showPage()
    c.save()
    return buffer.getvalue()


class QQSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_POST(self) -> None:
        if self.path != "/generate":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("content-length", "0"))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload.decode("utf-8"))
            pdf = build_pdf(data)
        except Exception as exc:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8"))
            return

        recipient = safe_filename(unquote(str(data.get("recipient", "請求書"))))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        encoded_name = quote(f"QQS_{recipient}.pdf")
        self.send_header("Content-Disposition", f"attachment; filename=\"QQS_invoice.pdf\"; filename*=UTF-8''{encoded_name}")
        self.send_header("Content-Length", str(len(pdf)))
        self.end_headers()
        self.wfile.write(pdf)


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), QQSHandler)
    print(f"QQS is running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
