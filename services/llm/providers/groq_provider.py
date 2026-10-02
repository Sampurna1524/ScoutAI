import os
import json

from groq import Groq

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


class GroqProvider(LLMProvider):

    name = "Groq"

    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    )

    supports_json = True

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise AuthenticationError(
                "Missing GROQ_API_KEY environment variable."
            )

        self.client = Groq(api_key=api_key)

    def extract_job(self, page_text: str) -> Job:

        prompt = JOB_EXTRACTION_PROMPT.format(page_text=page_text[:12000])

        try:

            response = self.client.chat.completions.create(

                model=self.model,

                temperature=0,

                response_format={
                    "type": "json_object"
                },

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content

            if not content:
                raise InvalidResponseError(
                    "Groq returned an empty response."
                )

            data = json.loads(content)

            return Job(**data)

        except json.JSONDecodeError as e:

            raise InvalidResponseError(
                f"Invalid JSON returned by Groq: {e}"
            )

        except Exception as e:

            message = str(e).lower()

            if "quota" in message:
                raise QuotaExceededError(str(e))

            if "rate limit" in message:
                raise RateLimitError(str(e))

            if "429" in message:
                raise RateLimitError(str(e))

            if "api key" in message:
                raise AuthenticationError(str(e))

            if "unauthorized" in message:
                raise AuthenticationError(str(e))

            if "503" in message:
                raise ProviderUnavailableError(str(e))

            raise