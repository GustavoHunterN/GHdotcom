"""
Flask app: home reads only from MySQL (no sync, no GitHub on request).
Run: flask --app app run   or   python app.py
"""

import logging
import os

from flask import Flask, render_template

from services.repo_catalog import load_repos_for_home

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)


def _home_limit_from_env() -> int | None:
    """
    HOME_REPO_LIMIT: number of repos, or 'all' / empty to use HOME_REPO_MAX inside list_repos.
    """
    raw = os.getenv("HOME_REPO_LIMIT", "100").strip()
    if not raw or raw.lower() in ("all", "none"):
        return None
    return int(raw)


@app.route("/")
def home():
    """Renderiza el showcase full-screen; solo lectura desde la DB."""
    log.info("GET / — home showcase")
    limit = _home_limit_from_env()
    try:
        repos = load_repos_for_home(limit=limit)
        return render_template("home.html", repos=repos, db_error=None)
    except (ConnectionError, OSError):
        log.exception("Home: fallo de conexión o I/O al cargar repos")
        return (
            render_template(
                "home.html",
                repos=[],
                db_error="Comprobá que MySQL esté en marcha y que las variables DB_* en .env sean correctas.",
            ),
            503,
        )
    except Exception:
        log.exception("Home: error al consultar repositorios")
        return (
            render_template(
                "home.html",
                repos=[],
                db_error="Ocurrió un error al leer la base de datos. Revisá los logs del servidor.",
            ),
            503,
        )


def main() -> None:
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
