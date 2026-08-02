"""Environment configuration for the Invoice Extractor."""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
TESSERACT_PATH = os.environ.get("TESSERACT_PATH", "tesseract")

UPLOAD_DIR = "uploads"

GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
OAUTH_CLIENT_SECRET_FILE = "credentials/client_secret.json"
OAUTH_TOKEN_FILE = "credentials/token.json"