# GHdotcom

Personal project: Python tools that sync GitHub repository metadata into MySQL using the [GitHub REST API](https://docs.github.com/en/rest), dynamic table creation, and inserts into a `repos` table.

**Repository:** [github.com/GustavoHunterN/GHdotcom](https://github.com/GustavoHunterN/GHdotcom)

## Features

- **`GitHubClient`** (`API_GitHub/GithubClient.py`) — HTTP only; errores tipados en `API_GitHub/errors.py` (`GitHubRequestError`, `GitHubResponseError`, `GitHubAuthError`, `GitHubNotFoundError`). Métodos: `list_repository_entries()`, `fetch_repository_by_full_name()`, etc.
- **`Repo`** (`API_GitHub/repo.py`) — Model only: `from_github(payload)`, `as_db_row()` for persistence.
- **`DatabaseConnector`** (`DB/connector.py`) — MySQL connection, `list_stored_repo_ids()`, `list_stored_repo_updated_at()`, `ensure_repos_table_for_row()`, `insert_repo_row()`, `update_repo_row()`, `upsert_repo_row()` (`INSERT ... ON DUPLICATE KEY UPDATE`).
- **`RepoSyncService`** (`sync/sync_service.py`) — Sincroniza por **id** de GitHub con un solo camino SQL (`upsert_repo_row`). Omite escrituras cuando el `updated_at` del API no es más reciente que el guardado (comparación de strings ISO); no hay diff campo a campo todavía.
- **Flask web** (`app.py`) — `GET /` renders un showcase full-screen (`templates/home.html` + `static/style.css` + `static/home.js`): solo lectura desde `DatabaseConnector.list_repos()`; sin sync al arrancar. Lógica fina en `services/repo_catalog.py`.

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
| `GITHUB_OWNER`   | Login for `/repos/{owner}/…` | resolved via `GET /user` if omitted |
| `DB_HOST`        | MySQL host               | `localhost` |
| `DB_PORT`        | MySQL port               | `3306` |
| `DB_USER`        | MySQL user               | _(from `.env`)_ |
| `DB_PASSWORD`    | MySQL password           | _(required)_ |
| `DB_NAME`        | Database name            | e.g. `GH`   |
| `FLASK_PORT`     | HTTP port for `app.py`   | `5000`      |
| `FLASK_DEBUG`    | Set `1` for Flask debug  | off         |
| `HOME_REPO_LIMIT` | Cuántos repos cargar en la home (`all` = usar `HOME_REPO_MAX`) | `100` |
| `HOME_REPO_MAX`   | Tope cuando `HOME_REPO_LIMIT=all` (también usado por `list_repos(None)`) | `100` |

## Usage

### Sync (GitHub → MySQL)

From the **project root**:

```bash
python -m sync
```

This loads **all** repository objects from GitHub (paginated), compares **`repos.id`** with GitHub’s numeric id, **inserts** new repos and **updates** existing rows with the latest JSON. Repos without `id` are skipped (warning in logs). If MySQL is not running, you will get a clear connection error (e.g. macOS error 61 → nothing listening on `DB_HOST`:`DB_PORT`).

**Clean resync (drop local copy, then fill again):** borra la tabla `repos` y vuelve a insertar todo lo que devuelva GitHub (útil si cambió el esquema o querés datos alineados al API actual).

```bash
python -m sync --fresh
```

La capa DB también **añade columnas** que falten si un repo trae campos nuevos respecto a la tabla ya creada (p. ej. `temp_clone_token`), sin necesidad de `--fresh` cada vez.

### Web home (showcase full-screen, solo lectura desde la DB)

La home **no** llama a GitHub. Cada repositorio ocupa una sección de altura completa (~100vh) con scroll tipo landing; animación suave al entrar en vista (IntersectionObserver). Incluye mockup visual si no hay imagen; si más adelante mapeás `preview_image_url` u `og_image_url` en `list_repos`, se puede usar como captura.

```bash
flask --app app run
# o: python app.py
```

Abrí `http://127.0.0.1:5000/` en el navegador. Para listar todos los repos hasta `HOME_REPO_MAX`: `HOME_REPO_LIMIT=all` en `.env`.

### Tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```
GHdotcom/
├── API_GitHub/
│   ├── GithubClient.py   # GitHub API client
│   ├── errors.py         # GitHubClientError hierarchy
│   └── repo.py           # Repo model and persistence
├── DB/
│   └── connector.py      # MySQL connector + repo table helpers
├── sync/
│   ├── sync_service.py   # RepoSyncService orchestration
│   └── __main__.py       # CLI: python -m sync
├── services/
│   └── repo_catalog.py   # load_repos_for_home() — DB read for UI
├── templates/
│   └── home.html         # Home HTML
├── static/
│   ├── style.css         # Showcase layout + mockup
│   └── home.js           # Scroll reveal (IntersectionObserver)
├── tests/
│   └── test_app.py
├── app.py                # Flask: GET / → home template
├── requirements.txt
├── .env.example
├── CHANGELOG.md
├── SECURITY.md
└── README.md
```

## Architecture notes

- **Table `repos`** — Columns follow the first persisted object: `id` is `VARCHAR(255) PRIMARY KEY`, other fields are `TEXT`. Complex values are serialized for insert.
- **Extending the client** — Add methods on `GitHubClient` and keep the base URL and headers in one place.
- **Pagination** — `GET /user/repos` is followed page by page (`per_page=100`) until all repos are loaded.

## Security

Do not commit `.env` or tokens. See [SECURITY.md](SECURITY.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

Personal / learning use. Add an explicit license if you publish the project more broadly.
