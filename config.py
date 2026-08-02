"""Environment configuration for the Invoice Extractor."""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
TESSERACT_PATH = os.environ.get("TESSERACT_PATH", "tesseract")

UPLOAD_DIR = "uploads"