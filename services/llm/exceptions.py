class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""
    pass


class QuotaExceededError(LLMProviderError):
    """Provider quota exhausted."""
    pass


class RateLimitError(LLMProviderError):
    """Provider rate limit exceeded."""
    pass


class AuthenticationError(LLMProviderError):
    """Invalid API key or authentication failure."""
    pass


class ProviderUnavailableError(LLMProviderError):
    """Provider service unavailable."""
    pass


class InvalidResponseError(LLMProviderError):
    """Provider returned an invalid response."""
    pass

class AllProvidersFailedError(LLMProviderError):
    pass