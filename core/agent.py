import os
from google import genai
from google.genai import types
from config import API_KEY, MODEL_NAME
import time


class AIAgent:
    def __init__(self, role_name, persona_path, temperature=0.7):
        self.role_name = role_name
        self.temperature = temperature
        self.system_prompt = self._load_prompt(persona_path)

    def _load_prompt(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def execute_task(self, user_input, history_context="", retries=3, wait=10):
        # Client her çağrıda oluşturuluyor — API key o an okunuyor
        api_key = os.environ.get("GEMINI_API_KEY") or API_KEY
        client = genai.Client(api_key=api_key)

        full_input = f"{user_input}\n\n[COMPANY_MEMORY]\n{history_context}" if history_context else user_input

        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=full_input,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        temperature=self.temperature
                    )
                )
                return response.text
            except Exception as e:
                if attempt < retries - 1:
                    print(f"  API error ({attempt + 1}/{retries}): Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise