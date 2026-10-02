from abc import ABC, abstractmethod

from models.job import Job


class LLMProvider(ABC):

    name = "Unknown"

    model = "Unknown"

    supports_json = False

    @abstractmethod
    def extract_job(self, page_text: str) -> Job:
        """
        Extract structured job information from page text.
        """
        pass