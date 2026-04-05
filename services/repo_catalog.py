"""
Read-only access to stored repositories for the web UI.
Does not call GitHub or run sync.
"""

from DB.connector import DatabaseConnector


def load_repos_for_home(limit: int | None = None) -> list[dict]:
    """
    Return repo dicts for the home showcase.
    ``limit=None`` uses HOME_REPO_MAX (see DatabaseConnector.list_repos).
    """
    with DatabaseConnector() as db:
        return db.list_repos(limit=limit)
