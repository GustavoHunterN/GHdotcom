import argparse
import logging
import sys

from API_GitHub.errors import GitHubClientError
from API_GitHub.GithubClient import GitHubClient
from DB.connector import DatabaseConnector
from .sync_service import RepoSyncService


def _configure_logging() -> None:
    """Console logging for `python -m sync` (skip if root already has handlers)."""
    root = logging.getLogger()
    if root.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Sync GitHub repositories into MySQL (upsert by id; skip unchanged updated_at).",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Drop table `repos` first, then sync (clean resync; all rows re-fetched).",
    )
    args = parser.parse_args(argv)

    try:
        github = GitHubClient()
        with DatabaseConnector() as db:
            if args.fresh:
                log.info("Fresh resync: dropping existing `repos` table")
                db.drop_repos_table()
            service = RepoSyncService(github, db)
            service.run()
        return 0

    except ConnectionError as exc:
        log.error("Cannot connect to the database: %s", exc)
        return 1
    except GitHubClientError as exc:
        # Traceback usually already logged in RepoSyncService
        log.error("Sync stopped (GitHub): %s", exc)
        return 1
    except Exception:
        log.exception("Sync failed with an unexpected error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
