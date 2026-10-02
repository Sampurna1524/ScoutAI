from typing import Optional
import time

from services.llm.exceptions import (
    AuthenticationError,
    ProviderUnavailableError,
    QuotaExceededError,
    RateLimitError,
    InvalidResponseError,
    AllProvidersFailedError,
)

from services.llm.registry import get_provider_classes

from models.scout_session import ScoutSession
from models.job import Job


class LLMService:

    @classmethod
    def extract_job(cls, page_text: str, session: Optional[ScoutSession] = None) -> Job:
        """
        Extract a job from the page_text using registered providers.

        If `session` is provided, provider lifecycle events will be appended
        to `session.events`. Backward compatible: callers may pass no session.
        """

        errors: list[str] = []

        previous_provider_name: Optional[str] = None

        # Providers are tried in priority order
        for provider_cls in get_provider_classes():

            provider = provider_cls()

            provider_name = getattr(provider, "name", provider_cls.__name__)
            provider_model = getattr(provider, "model", None)

            # If switching from a previous provider, record the switch
            if session is not None and previous_provider_name and previous_provider_name != provider_name:
                session.append_event(
                    "provider_switch",
                    f"Switching from {previous_provider_name} to {provider_name}",
                    {"from": previous_provider_name, "to": provider_name},
                )

            # Provider start event
            if session is not None:
                session.append_event(
                    "provider_start",
                    f"Using {provider_name}",
                    {"provider": provider_name, "model": provider_model},
                )

            # Retry transient failures up to 2 attempts (initial + 1 retry)
            max_attempts = 2
            backoffs = [1, 2]

            attempt = 0
            while attempt < max_attempts:
                attempt += 1
                try:
                    result = provider.extract_job(page_text)

                    # success event
                    if session is not None:
                        session.append_event(
                            "provider_success",
                            f"{provider_name} extracted job successfully",
                            {"provider": provider_name},
                        )

                    return result

                except (QuotaExceededError, RateLimitError, ProviderUnavailableError) as e:

                    # Transient errors: may retry
                    if session is not None:
                        session.append_event(
                            "provider_failed",
                            f"{provider_name} failed: {e}",
                            {"provider": provider_name, "reason": str(e)},
                        )

                    # Decide whether to retry or stop
                    is_transient = isinstance(e, (RateLimitError, ProviderUnavailableError))

                    if is_transient and attempt < max_attempts:
                        backoff = backoffs[min(attempt - 1, len(backoffs) - 1)]
                        time.sleep(backoff)
                        continue
                    else:
                        errors.append(f"{provider_name}: {e}")
                        break

                except (AuthenticationError, InvalidResponseError) as e:

                    # Do not retry these errors; record and move on
                    if session is not None:
                        session.append_event(
                            "provider_failed",
                            f"{provider_name} failed: {e}",
                            {"provider": provider_name, "reason": str(e)},
                        )

                    errors.append(f"{provider_name}: {e}")
                    break

                except Exception as e:

                    # Unknown errors: record and continue to next provider
                    if session is not None:
                        session.append_event(
                            "provider_failed",
                            f"{provider_name} failed: {e}",
                            {"provider": provider_name, "reason": str(e)},
                        )

                    errors.append(f"{provider_name}: {e}")
                    break

            # after attempts, set previous provider name for next loop
            previous_provider_name = provider_name

        # All providers failed
        raise AllProvidersFailedError("\n".join(errors))