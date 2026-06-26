"""
Nura - AI Exceptions
Custom exception classes for the AI core infrastructure
"""

class AIError(Exception):
    """Base exception for all AI-related errors"""
    pass


class AIConfigurationError(AIError):
    """Raised when there is a configuration error with the AI service"""
    pass


class AIConnectionError(AIError):
    """Raised when connection to AI API fails"""
    pass


class AITimeoutError(AIError):
    """Raised when AI API request times out"""
    pass


class AIRateLimitError(AIError):
    """Raised when AI API rate limits are hit"""
    pass


class AIResponseError(AIError):
    """Raised when AI API returns an unexpected or error response"""
    pass


class EmbeddingError(AIError):
    """Base exception for all embedding-related errors"""
    pass


class EmbeddingConfigurationError(EmbeddingError):
    """Raised when there is a configuration error with the embedding service"""
    pass


class EmbeddingValidationError(EmbeddingError):
    """Raised when embedding validation fails (e.g. empty text, invalid dimensions)"""
    pass
