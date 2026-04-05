"""Typed errors for the GitHub HTTP client (sync and future retries / rate limits)."""


class GitHubClientError(Exception):
    """Base class for all failures raised by ``GitHubClient``."""

    pass


class GitHubRequestError(GitHubClientError):
    """
    Network failure: timeout, DNS, connection refused, or other transport errors
    before a complete HTTP response is available.
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
    ) -> None:
        self.operation = operation
        super().__init__(message)


class GitHubResponseError(GitHubClientError):
    """
    GitHub returned an HTTP status that is not success, or the body was not valid JSON,
    or JSON did not match the expected shape (list vs object).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        path: str | None = None,
        response_body_preview: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.path = path
        self.response_body_preview = response_body_preview
        super().__init__(message)


class GitHubAuthError(GitHubResponseError):
    """401 / 403 — invalid token, missing scopes, or insufficient permissions."""

    pass


class GitHubNotFoundError(GitHubResponseError):
    """404 — resource not found or not visible with this token."""

    pass
