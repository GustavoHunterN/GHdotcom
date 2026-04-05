from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from API_GitHub.errors import GitHubClientError
from API_GitHub.repo import Repo

if TYPE_CHECKING:
    from API_GitHub.GithubClient import GitHubClient
    from DB.connector import DatabaseConnector

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Outcome of a sync run: inserts/updates via upsert, plus skipped unchanged rows."""

    inserted: int = 0
    updated: int = 0
    skipped_unchanged: int = 0


class RepoSyncService:
    """Orchestrates: fetch GitHub repos → skip up-to-date rows → upsert the rest by ``id``."""

    def __init__(self, github: "GitHubClient", db: "DatabaseConnector") -> None:
        self._github = github
        self._db = db

    @staticmethod
    def _should_skip_unchanged(
        repo_id: str,
        payload: dict,
        stored_updated_at: dict[str, str],
    ) -> bool:
        """
        Skip DB write if we already have this id and GitHub ``updated_at`` is not newer than stored.
        GitHub uses ISO 8601 strings; lexicographic order matches time order for equal formatting.
        """
        remote_u = payload.get("updated_at")
        if not remote_u:
            return False
        if repo_id not in stored_updated_at:
            return False
        stored_u = stored_updated_at[repo_id]
        remote_s = str(remote_u)
        # stored >= remote → nothing newer from API
        return stored_u >= remote_s

    def run(self) -> SyncResult:
        result = SyncResult()

        logger.info("Starting repository sync")

        try:
            remote_payloads = self._github.fetch_authenticated_user_repositories()
        except GitHubClientError:
            logger.exception(
                "Aborting sync: failed to list repositories from GitHub "
                "(token, network, rate limit, or unexpected API response)"
            )
            raise

        logger.info("Fetched %d repos from GitHub", len(remote_payloads))

        try:
            stored_updated_at = self._db.list_stored_repo_updated_at()
        except Exception:
            logger.exception(
                "Aborting sync: failed to read stored repository metadata from the database"
            )
            raise

        logger.info(
            "Loaded %d stored updated_at values for skip-if-unchanged",
            len(stored_updated_at),
        )

        to_process: list[dict] = []
        for payload in remote_payloads:
            gid = payload.get("id")
            if gid is None:
                logger.warning(
                    "Skipping repository without GitHub id: name=%r full_name=%r",
                    payload.get("name"),
                    payload.get("full_name"),
                )
                continue
            sid = str(gid)
            if self._should_skip_unchanged(sid, payload, stored_updated_at):
                result.skipped_unchanged += 1
                logger.debug(
                    "Skip unchanged repo id=%s name=%r (updated_at)",
                    sid,
                    payload.get("name"),
                )
                continue
            to_process.append(payload)

        logger.info(
            "%d repos to upsert (%d skipped as already up to date)",
            len(to_process),
            result.skipped_unchanged,
        )

        for payload in to_process:
            name = payload.get("name", "?")
            rid = payload.get("id")
            try:
                repo = Repo.from_github(payload)
                row = repo.as_db_row()
                self._db.ensure_repos_table_for_row(row)
                rc = self._db.upsert_repo_row(row)
                if rc == 1:
                    result.inserted += 1
                elif rc == 2:
                    result.updated += 1
                else:
                    logger.warning(
                        "Unexpected upsert rowcount=%s for id=%r name=%r",
                        rc,
                        rid,
                        name,
                    )
            except Exception:
                logger.exception(
                    "Database or unexpected error while upserting repository id=%r name=%r",
                    rid,
                    name,
                )
                raise

        logger.info("Inserted %d repos", result.inserted)
        logger.info("Updated %d repos", result.updated)
        if result.skipped_unchanged:
            logger.info(
                "Skipped %d repos (unchanged updated_at vs database)",
                result.skipped_unchanged,
            )
        logger.info("Sync completed")
        return result

    def sync_stale_repositories(self) -> None:
        """Deprecated hook: full sync runs in ``run()``."""
        return
