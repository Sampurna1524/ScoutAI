import os
from google import genai
from google.genai import types

from models.job import Job

from services.llm.provider import LLMProvider
from services.llm.prompts import JOB_EXTRACTION_PROMPT
from services.llm.exceptions import (
    AuthenticationError,
    InvalidResponseError,
    ProviderUnavailableError,
    QuotaExceededError,
    RateLimitError,
)

class GeminiProvider(LLMProvider):
    name = "Gemini"
    supports_json = True

    def __init__(self):
        self.model = os.getenv(
                "GEMINI_MODEL",
                "gemini-2.5-flash"
            )

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise AuthenticationError(
                "Missing GEMINI_API_KEY"
            )

        self.client = genai.Client(
            api_key=api_key
        )

    def extract_job(self, page_text: str) -> Job:

        prompt = JOB_EXTRACTION_PROMPT.format(page_text=page_text[:12000])

        try:

            response = self.client.models.generate_content(

                model=self.model,

                contents=prompt,

                config=types.GenerateContentConfig(

                    response_mime_type="application/json",

                    response_schema=Job

                )

            )

            if response.parsed is None:
                raise InvalidResponseError(
                    "Gemini returned an empty response."
                )

            return response.parsed

        except InvalidResponseError:
            raise

        except Exception as e:

            message = str(e).lower()

            if "quota" in message:
                raise QuotaExceededError(str(e))

            if "resource_exhausted" in message:
                raise QuotaExceededError(str(e))

            if "429" in message:
                raise RateLimitError(str(e))

            if "api key" in message:
                raise AuthenticationError(str(e))

            if "unauthorized" in message:
                raise AuthenticationError(str(e))

            if "401" in message:
                raise AuthenticationError(str(e))

            if "503" in message:
                raise ProviderUnavailableError(str(e))

            raise