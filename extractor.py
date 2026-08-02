"""Extracts structured invoice/receipt data from an uploaded image or PDF."""

import json
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import GROQ_API_KEY, TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0,
)

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are an invoice/receipt data extraction assistant.
Given raw OCR text from a receipt or invoice, extract the following fields as JSON:
- vendor: the business/store name
- date: the transaction/invoice date (as written)
- total_amount: the total amount paid (number only, no currency symbol)
- currency: the currency if identifiable (e.g. PKR, USD), else null
- items: a list of line items, each with "description" and "amount" if identifiable (else empty list)

IMPORTANT rules for line items:
- Invoice tables often start each row with a serial/row number (1, 2, 3...) in its own column.
  This is NOT part of the item description — ignore it and use only the actual item/description text.
- OCR sometimes merges the serial number into the description (e.g. "i 10 Days" or "2 Steel Structure Installation 5 Weeks").
  In that case, strip the leading number/stray character and reconstruct the real description.
- Quantity/duration text (like "10 Days", "5 Weeks", "200 Cubics") is part of the item's detail, not the row number.
- If a row shows unit price AND a total (e.g. "$100 $1,000"), use the LAST number as the item's amount (that's the line total).
- Never invent items or amounts that aren't supported by the OCR text.

Respond with ONLY valid JSON, no explanation, no markdown formatting.
If a field cannot be determined, use null (or empty list for items)."""),
        ("human", "OCR text:\n\n{ocr_text}"),
    ]
)

extraction_chain = EXTRACTION_PROMPT | llm | StrOutputParser()


def extract_text(file_path: str) -> str:
    """OCR: pulls raw text out of an image or PDF (no preprocessing — kept simple/reliable)."""
    if file_path.lower().endswith(".pdf"):
        pages = convert_from_path(file_path)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
        return text
    else:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)


def extract_structured_data(file_path: str) -> dict:
    """Full pipeline: OCR -> LLM structuring -> dict."""
    ocr_text = extract_text(file_path)

    if not ocr_text.strip():
        raise ValueError("No text could be read from this file.")

    raw_json = extraction_chain.invoke({"ocr_text": ocr_text})

    cleaned = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON: {cleaned[:200]}")

    data["ocr_text_preview"] = ocr_text[:300]
    return data


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <path_to_receipt>")
    else:
        result = extract_structured_data(sys.argv[1])
        print(json.dumps(result, indent=2))