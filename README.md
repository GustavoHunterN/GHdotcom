# GHdotcom

Personal project: Python tools that sync GitHub repository metadata into MySQL using the [GitHub REST API](https://docs.github.com/en/rest), dynamic table creation, and inserts into a `repos` table.

**Repository:** [github.com/GustavoHunterN/GHdotcom](https://github.com/GustavoHunterN/GHdotcom)

## Features

- **`GitHubClient`** (`API_GitHub/GithubClient.py`) — Single place for GitHub API calls: `get_repos()`, `get_repo_names()`, and `get_repo_by_name(name)` (uses `GET /repos/{owner}/{repo}`). Extend this class when you add more endpoints.
- **`Repo`** (`API_GitHub/repo.py`) — Maps API fields to attributes, `CREATE TABLE IF NOT EXISTS repos`, `repo_in_db()`, and `save()`.
- **`DatabaseConnector`** (`DB/connector.py`) — MySQL connection plus `get_repos()` returning repository names already stored.
- **`Logic`** (`Logic/Logic.py`) — Compares GitHub with the database and inserts missing repositories.

## Requirements

- Python 3.10+
- MySQL with a database you can use for the `repos` table (for example `GH` or any name set in `.env`)
- A [GitHub personal access token](https://github.com/settings/tokens) with scopes that allow listing your repositories

## Installation

```bash
git clone https://github.com/GustavoHunterN/GHdotcom.git
cd GHdotcom
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set variables (see **Configuration**).

Create the database in MySQL if it does not exist:

```sql
CREATE DATABASE GH CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Configuration

| Variable         | Description              | Default     |
|------------------|--------------------------|-------------|
| `GITHUB_TOKEN`   | GitHub PAT               | _(required)_ |
| `DB_HOST`        | MySQL host               | _(from `.env`)_ |
| `DB_USER`        | MySQL user               | _(from `.env`)_ |
| `DB_PASSWORD`    | MySQL password           | _(required)_ |
| `DB_NAME`        | Database name            | e.g. `GH`   |

Set `GitHubClient.user` to your GitHub username or organization so API paths resolve correctly.

## Usage

From the **project root**:

```bash
python -m Logic.Logic
```

This resolves which repository names exist on GitHub but not in MySQL, fetches each full repository object from the API, and inserts rows when not already present.

## Project layout

```
GHdotcom/
├── API_GitHub/
│   ├── GithubClient.py   # GitHub API client
│   └── repo.py           # Repo model and persistence
├── DB/
│   └── connector.py      # MySQL connector
├── Logic/
│   └── Logic.py          # Entry: diff GitHub vs DB, insert missing
├── requirements.txt
├── .env.example
├── CHANGELOG.md
├── SECURITY.md
└── README.md
```

## Architecture notes

- **Table `repos`** — Columns follow the first persisted object: `id` is `VARCHAR(255) PRIMARY KEY`, other fields are `TEXT`. Complex values are serialized for insert.
- **Extending the client** — Add methods on `GitHubClient` and keep `BASE_URL` and headers in one place.

## Security

Do not commit `.env` or tokens. See [SECURITY.md](SECURITY.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

Personal / learning use. Add an explicit license if you publish the project more broadly.
