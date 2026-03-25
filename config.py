from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")
BASE_PROJECT_PATH = os.getenv("BASE_PROJECT_PATH", "projects")
COMPANY_VAULT_PATH = os.getenv("COMPANY_VAULT_PATH", "company_pyvault")
LANGUAGE = os.getenv("LANGUAGE", "English")