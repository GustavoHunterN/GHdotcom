"""
Tests for ``RepoSyncService.run()`` — sync orchestration with mocked GitHub and MySQL.

Covers: new inserts, skip unchanged ``updated_at``, updates when newer, invalid payloads,
and GitHub client failures. No real HTTP or database.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from API_GitHub.errors import GitHubAuthError, GitHubClientError
from sync.sync_service import RepoSyncService, SyncResult


def _payload(
    *,
    repo_id: int | str | None,
    name: str,
    updated_at: str | None = "2024-06-01T12:00:00Z",
    **extra: str | int | None,
) -> dict:
    """Minimal GitHub repository object for ``Repo.from_github`` / sync."""
    p: dict = {"name": name, "full_name": f"owner/{name}", **extra}
    if repo_id is not None:
        p["id"] = repo_id
    if updated_at is not None:
        p["updated_at"] = updated_at
    return p


@pytest.fixture
def mock_github() -> MagicMock:
    return MagicMock(name="GitHubClient")


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(name="DatabaseConnector")


@pytest.fixture
def service(mock_github: MagicMock, mock_db: MagicMock) -> RepoSyncService:
    return RepoSyncService(mock_github, mock_db)


class TestRepoSyncServiceRun:
    def test_inserts_new_repositories_and_counts_them(
        self, service: RepoSyncService, mock_github: MagicMock, mock_db: MagicMock
    ) -> None:
        """GitHub returns repos unknown to DB → upsert runs; rowcount 1 → inserted tally."""
        mock_github.fetch_authenticated_user_repositories.return_value = [
            _payload(repo_id=101, name="alpha"),
            _payload(repo_id=102, name="beta"),
        ]
        mock_db.list_stored_repo_updated_at.return_value = {}
        mock_db.upsert_repo_row.side_effect = [1, 1]

        result = service.run()

        assert result == SyncResult(inserted=2, updated=0, skipped_unchanged=0)
        assert mock_db.upsert_repo_row.call_count == 2
        assert mock_db.ensure_repos_table_for_row.call_count == 2

    def test_skips_unchanged_when_stored_updated_at_is_same_or_newer(
        self, service: RepoSyncService, mock_github: MagicMock, mock_db: MagicMock
    ) -> None:
        """Stored ``updated_at`` >= API → no write; ``skipped_unchanged`` increments."""
        ts = "2024-06-01T12:00:00Z"
        mock_github.fetch_authenticated_user_repositories.return_value = [
            _payload(repo_id=201, name="same", updated_at=ts),
        ]
        mock_db.list_stored_repo_updated_at.return_value = {"201": ts}

        result = service.run()

        assert result == SyncResult(inserted=0, updated=0, skipped_unchanged=1)
        mock_db.ensure_repos_table_for_row.assert_not_called()
        mock_db.upsert_repo_row.assert_not_called()

    def test_updates_when_remote_updated_at_is_newer(
        self, service: RepoSyncService, mock_github: MagicMock, mock_db: MagicMock
    ) -> None:
        """Same id, newer ``updated_at`` from API → upsert with rowcount 2 → updated tally."""
        mock_github.fetch_authenticated_user_repositories.return_value = [
            _payload(
                repo_id=301,
                name="moved",
                updated_at="2024-08-01T00:00:00Z",
            ),
        ]
        mock_db.list_stored_repo_updated_at.return_value = {
            "301": "2024-01-01T00:00:00Z",
        }
        mock_db.upsert_repo_row.return_value = 2

        result = service.run()

        assert result == SyncResult(inserted=0, updated=1, skipped_unchanged=0)
        mock_db.upsert_repo_row.assert_called_once()

    def test_payload_without_id_is_skipped_and_does_not_abort_sync(
        self,
        service: RepoSyncService,
        mock_github: MagicMock,
        mock_db: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Missing ``id`` → warning, rest of list still processed."""
        mock_github.fetch_authenticated_user_repositories.return_value = [
            {"name": "bad", "full_name": "owner/bad", "updated_at": "2024-06-01T12:00:00Z"},
            _payload(repo_id=401, name="good"),
        ]
        mock_db.list_stored_repo_updated_at.return_value = {}
        mock_db.upsert_repo_row.return_value = 1

        caplog.set_level(logging.WARNING, logger="sync.sync_service")

        result = service.run()

        assert result.inserted == 1
        assert "Skipping repository without GitHub id" in caplog.text
        mock_db.upsert_repo_row.assert_called_once()

    def test_github_client_error_propagates_and_db_not_read(
        self, service: RepoSyncService, mock_github: MagicMock, mock_db: MagicMock
    ) -> None:
        """``GitHubClientError`` from fetch aborts sync loudly; DB metadata not loaded."""
        mock_github.fetch_authenticated_user_repositories.side_effect = GitHubAuthError(
            "unauthorized", status_code=401, path="/user/repos"
        )

        with pytest.raises(GitHubClientError) as exc_info:
            service.run()

        assert "unauthorized" in str(exc_info.value)
        mock_db.list_stored_repo_updated_at.assert_not_called()
        mock_db.upsert_repo_row.assert_not_called()
