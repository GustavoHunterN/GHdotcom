import logging
import os
from typing import Any, Literal, cast

import requests
from dotenv import load_dotenv

from API_GitHub.errors import (
    GitHubAuthError,
    GitHubNotFoundError,
    GitHubRequestError,
    GitHubResponseError,
)

logger = logging.getLogger(__name__)

_PER_PAGE = 100
_BODY_PREVIEW = 600


class GitHubClient:
    """HTTP client for the GitHub REST API only (no database access)."""

    def __init__(self) -> None:
        try:
            load_dotenv()
        except OSError as exc:
            logger.warning("Could not load .env: %s", exc)

        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }
        self.base_url = "https://api.github.com"
        self._owner_login: str | None = os.getenv("GITHUB_OWNER") or None

    def _send_get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        operation: str,
    ) -> requests.Response:
        """Perform GET; maps timeouts and connection failures to ``GitHubRequestError``."""
        url = f"{self.base_url}{path}"
        try:
            return requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=30,
            )
        except requests.Timeout as exc:
            raise GitHubRequestError(
                f"Request timed out (30s) during {operation}",
                operation=operation,
            ) from exc
        except requests.ConnectionError as exc:
            raise GitHubRequestError(
                f"Connection error during {operation}: {exc}",
                operation=operation,
            ) from exc
        except requests.RequestException as exc:
            raise GitHubRequestError(
                f"HTTP request failed during {operation}: {exc}",
                operation=operation,
            ) from exc

    def _parse_success_json(
        self,
        response: requests.Response,
        *,
        expect: Literal["list", "object"],
        operation: str,
    ) -> list | dict:
        """
        Validate HTTP status and JSON shape for a successful GitHub API response.
        Raises typed ``GitHub*Error`` subclasses on failure.
        """
        status = response.status_code
        url = response.url
        preview = (response.text or "")[:_BODY_PREVIEW]

        if status == 401:
            raise GitHubAuthError(
                f"GitHub authentication failed ({operation}): invalid or expired token (HTTP 401).",
                status_code=401,
                path=url,
                response_body_preview=preview,
            )
        if status == 403:
            raise GitHubAuthError(
                f"GitHub access forbidden ({operation}): token may lack required scopes (HTTP 403).",
                status_code=403,
                path=url,
                response_body_preview=preview,
            )
        if status == 404:
            raise GitHubNotFoundError(
                f"GitHub resource not found ({operation}) (HTTP 404).",
                status_code=404,
                path=url,
                response_body_preview=preview,
            )
        if status == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise GitHubResponseError(
                f"GitHub rate limit exceeded ({operation}). Retry-After: {retry_after} s. "
                "Wait and retry, or add backoff (HTTP 429).",
                status_code=429,
                path=url,
                response_body_preview=preview,
            )
        if status >= 500:
            raise GitHubResponseError(
                f"GitHub server error during {operation} (HTTP {status}).",
                status_code=status,
                path=url,
                response_body_preview=preview,
            )
        if status != 200:
            raise GitHubResponseError(
                f"Unexpected HTTP {status} during {operation}.",
                status_code=status,
                path=url,
                response_body_preview=preview,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise GitHubResponseError(
                f"Response body is not valid JSON ({operation}): {exc}",
                status_code=status,
                path=url,
                response_body_preview=preview,
            ) from exc

        if expect == "list":
            if not isinstance(data, list):
                raise GitHubResponseError(
                    f"Expected a JSON array for {operation}, got {type(data).__name__}",
                    status_code=status,
                    path=url,
                    response_body_preview=preview,
                )
            return data
        if not isinstance(data, dict):
            raise GitHubResponseError(
                f"Expected a JSON object for {operation}, got {type(data).__name__}",
                status_code=status,
                path=url,
                response_body_preview=preview,
            )
        return data

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        expect: Literal["list", "object"],
        operation: str,
    ) -> list | dict:
        response = self._send_get(path, params=params, operation=operation)
        return self._parse_success_json(response, expect=expect, operation=operation)

    def owner_login(self) -> str:
        """Login for the authenticated user (GET /user). Used when only the short name is known."""
        if self._owner_login is None:
            data = cast(
                dict[str, Any],
                self._get_json(
                    "/user",
                    expect="object",
                    operation="GET /user (resolve owner login)",
                ),
            )
            login = data.get("login")
            if not login:
                raise GitHubResponseError(
                    "GET /user returned 200 but JSON has no 'login' field.",
                    status_code=200,
                    path=f"{self.base_url}/user",
                )
            self._owner_login = str(login)
        return self._owner_login

    def fetch_authenticated_user_repositories(self) -> list[dict]:
        """
        GET /user/repos — all repositories visible to the token, following pagination.
        """
        logger.info("Fetching repositories from GitHub with pagination")

        all_items: list[dict] = []
        page = 1

        while True:
            params = {"per_page": _PER_PAGE, "page": page}
            operation = f"GET /user/repos (page {page})"
            data = cast(
                list,
                self._get_json(
                    "/user/repos",
                    params=params,
                    expect="list",
                    operation=operation,
                ),
            )

            chunk_len = len(data)
            logger.info(
                "Fetched page %d with %d repositories",
                page,
                chunk_len,
            )
            all_items.extend(data)

            if chunk_len == 0:
                break
            if chunk_len < _PER_PAGE:
                break
            page += 1

        merged = self._dedupe_repository_list(all_items)
        logger.info(
            "Pagination completed. Total repositories fetched: %d",
            len(merged),
        )
        return merged

    @staticmethod
    def _dedupe_repository_list(items: list[dict]) -> list[dict]:
        """Keep first occurrence per ``full_name`` (or ``id``) to avoid accidental duplicates."""
        seen: set[str] = set()
        out: list[dict] = []
        for item in items:
            fn = item.get("full_name")
            rid = item.get("id")
            key = str(fn) if fn is not None else f"id:{rid}"
            if key in seen:
                logger.warning(
                    "Skipping duplicate repository entry while merging pages: %s",
                    key,
                )
                continue
            seen.add(key)
            out.append(item)
        return out

    def list_repository_entries(self) -> list[dict[str, str]]:
        """
        Each repo as ``name`` (short slug) and ``full_name`` (``owner/repo``).
        Use ``full_name`` for GET /repos/{owner}/{repo} so org/collab repos resolve correctly.
        """
        out: list[dict[str, str]] = []
        for item in self.fetch_authenticated_user_repositories():
            full_name = item.get("full_name")
            name = item.get("name")
            if full_name and name:
                out.append({"name": str(name), "full_name": str(full_name)})
        return out

    def list_repository_names(self) -> list[str]:
        """Short repository names only (same order as ``list_repository_entries``)."""
        return [e["name"] for e in self.list_repository_entries()]

    def fetch_repository_by_full_name(self, full_name: str) -> dict:
        """GET /repos/{owner}/{repo} using the ``owner/repo`` string from the API."""
        full_name = full_name.strip()
        if "/" not in full_name:
            raise ValueError(
                f"full_name must look like 'owner/repo', got {full_name!r}"
            )
        owner, _, repo = full_name.partition("/")
        if not owner or not repo or "/" in repo:
            raise ValueError(f"Invalid full_name: {full_name!r}")
        path = f"/repos/{owner}/{repo}"
        operation = f"GET {path} (repository {full_name!r})"
        return cast(
            dict[str, Any],
            self._get_json(path, expect="object", operation=operation),
        )

    def fetch_repository(self, name: str) -> dict:
        """
        GET /repos/{authenticated_user}/{name}.
        Prefer ``fetch_repository_by_full_name`` when the owner may not be the logged-in user.
        """
        owner = self.owner_login()
        path = f"/repos/{owner}/{name}"
        operation = f"GET {path} (repository name={name!r})"
        return cast(
            dict[str, Any],
            self._get_json(path, expect="object", operation=operation),
        )
