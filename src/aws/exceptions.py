"""Custom exceptions for AWS operations."""


class AWSError(Exception):
    """Base exception for AWS-related errors."""
    pass


class AWSCredentialsError(AWSError):
    """Raised when AWS credentials are invalid or missing."""
    pass


class AWSPermissionError(AWSError):
    """Raised when AWS permissions are insufficient."""
    pass


class AWSServiceError(AWSError):
    """Raised when AWS service calls fail."""
    pass


class AWSResourceNotFoundError(AWSError):
    """Raised when AWS resources are not found."""
    pass