# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Sync by GitHub `id`:** `RepoSyncService` uses `DatabaseConnector.upsert_repo_row()` (`INSERT ... ON DUPLICATE KEY UPDATE`) instead of separate insert/update. Rows whose GitHub `updated_at` is not newer than the stored value are skipped (string compare on ISO timestamps). Single pass over `fetch_authenticated_user_repositories()` (no per-repo GET); no field-level diff yet.

### Added

- `DatabaseConnector.list_stored_repo_updated_at()` and `upsert_repo_row()` for sync efficiency; `SyncResult.skipped_unchanged` counts repos skipped as already up to date.

- Typed GitHub errors (`API_GitHub/errors.py`): centralized GET + JSON validation in `GithubClient` (timeouts, HTTP 401/403/404/429/5xx, invalid JSON); `RepoSyncService` / CLI catch `GitHubClientError` without duplicating tracebacks.
- `GitHubClient.fetch_authenticated_user_repositories()` paginates `/user/repos` (up to 100 per page) with logging; dedupe by `full_name`/`id` when merging pages.
- `python -m sync --fresh`: drops `repos` then runs sync (clean resync).
- `DatabaseConnector.drop_repos_table()` and schema extension: missing columns are added with `ALTER TABLE` before insert when GitHub returns new fields.

### Fixed

- Sync uses `full_name` (`owner/repo`) from GitHub to fetch each repository, fixing 404s for org and non–user-owned repos.
- Home showcase: full-viewport sections per repo, scroll-snap + IntersectionObserver reveal (`static/home.js`), mockup preview panel; hero landing; optional `homepage`, `full_name`, `preview_image_url` / `og_image_url` when present in DB.
- `DatabaseConnector.list_repos(limit=None)` uses `HOME_REPO_MAX`; `HOME_REPO_LIMIT` / `all` in `app.py` for how many repos to render.
- Controlled errors and logging on DB failures (`503` + user-safe message).

### Changed

- Replaced `Logic` with package `sync`: `RepoSyncService` in `sync/sync_service.py`, entry point `python -m sync` (`sync/__main__.py` with `if __name__ == "__main__"`).
- `GitHubClient` is HTTP-only; `Repo` is a model (`from_github`, `as_db_row`); table creation and inserts live in `DatabaseConnector`.
- Clearer MySQL connection errors for unreachable servers (e.g. errno 2003 / macOS 61); optional `DB_PORT` and `GITHUB_OWNER` in `.env.example`.

## [0.2.0] - 2026-03-28

### Added

- `Logic` module: `repo_missing_in_db()` and `add_repo_to_db()` to sync repositories missing from MySQL.
- `GitHubClient.get_repo_names()` and `get_repo_by_name()` for listing names and fetching a single repository.
- `DatabaseConnector.get_repos()` to list repository names already stored.
- `Repo.repo_in_db()` to skip duplicates before insert.

### Changed

- Project layout: `API_GitHub/` for the GitHub client and `Repo` model, `DB/connector.py` for MySQL, entry point `python -m Logic.Logic`.
- Documentation updated for [GustavoHunterN/GHdotcom](https://github.com/GustavoHunterN/GHdotcom).

### Fixed

- `GET` URL for a single repository: use `/repos/{owner}/{repo}` per GitHub API.

## [0.1.0] - 2026-03-28

### Added

- Initial GitHub → MySQL sync, `GitHubClient`, `Repo`, and `DatabaseConnector`.
- Baseline documentation and security notes.
