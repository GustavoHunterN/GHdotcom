# GHdotcom

Proyecto personal para mostrar y mejorar habilidades: herramientas en Python que sincronizan la información de tus repositorios de GitHub con una base de datos MySQL (APIs, modelado dinámico de tablas y persistencia).

## Requisitos

- Python 3.10+
- MySQL con una base llamada `GH` (o el nombre que definas en variables de entorno)
- [Token de acceso personal de GitHub](https://github.com/settings/tokens) con permisos que permitan listar tus repositorios

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y configura las variables (ver sección **Configuración**).

Crea la base de datos en MySQL si aún no existe:

```sql
CREATE DATABASE GH CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Configuración

| Variable        | Descripción                          | Por defecto   |
|----------------|--------------------------------------|---------------|
| `GITHUB_TOKEN` | Token PAT de GitHub                  | _(obligatorio)_ |
| `DB_HOST`      | Host de MySQL                        | `localhost`   |
| `DB_USER`      | Usuario MySQL                        | `root`        |
| `DB_PSSWD`     | Contraseña MySQL                     | _(obligatorio)_ |
| `DB_NAME`      | Nombre de la base de datos           | `GH`          |

## Uso

Desde la raíz del proyecto:

```bash
python -m GH.GH
```

El script:

1. Valida el token contra la API de GitHub (`GET /user`).
2. Obtiene la lista de repositorios (`GET /user/repos`).
3. Por cada repositorio, crea (si no existe) la tabla `repo` con columnas según los campos del JSON de la API e inserta los registros con `INSERT IGNORE`.

## Estructura del proyecto

```
GHdotcom/
├── DB/
│   └── Conector.py      # Conexión MySQL y utilidades CRUD básicas
├── GH/
│   └── GH.py            # Punto de entrada: GitHub API → MySQL
├── modules/
│   └── repo.py          # Modelo `Repo` y persistencia dinámica
├── control/
│   └── classes.py       # Validación de objetos
├── requirements.txt
├── .env.example
├── CHANGELOG.md
└── README.md
```

## Seguridad

- **No subas** el archivo `.env` ni tokens; está excluido en `.gitignore`.
- Si un token o contraseña llegó a exponerse en un chat, commit o captura, **revócalo o cámbialo** de inmediato en GitHub y en MySQL.
- Más detalle en [SECURITY.md](SECURITY.md).

## Changelog

Historial de versiones en [CHANGELOG.md](CHANGELOG.md).

## Licencia

Uso personal / aprendizaje. Ajusta la licencia si publicas el proyecto de forma abierta.
