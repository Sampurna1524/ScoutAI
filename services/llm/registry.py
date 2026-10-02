import os

from services.llm.providers.gemini_provider import GeminiProvider
from services.llm.providers.groq_provider import GroqProvider


_PROVIDER_MAP = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


def get_provider_classes():
    """
    Returns provider classes in the order specified
    by the LLM_PRIORITY environment variable.
    """

    priority = os.getenv(
        "LLM_PRIORITY",
        "gemini,groq"
    )

    providers = []

    for name in priority.split(","):

        name = name.strip().lower()

        if name in _PROVIDER_MAP:
            providers.append(_PROVIDER_MAP[name])

    return providers