# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
