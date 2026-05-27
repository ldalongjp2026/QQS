from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import build_pdf


def test_pdf_generation():
    pdf = build_pdf(
        {
            "recipient": "京嵐株式会社",
            "subject": "庭の手入れ 人工費",
            "amount": "400000",
            "taxStatus": "要確認",
            "invoiceNo": "なし",
            "issueDate": "2026年5月26日",
            "dueDate": "2026年6月1日",
            "item": "庭の手入れ 人工費",
            "quantity": "1式",
        }
    )
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000


if __name__ == "__main__":
    test_pdf_generation()
    print("PDF smoke test passed")
