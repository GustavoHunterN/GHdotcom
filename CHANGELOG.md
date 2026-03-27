# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [Unreleased]

## [0.1.0] - 2026-03-27

### Añadido

- Script `GH/GH.py` que consulta la API de GitHub y persiste repositorios en MySQL.
- Modelo `Repo` (`modules/repo.py`) con creación dinámica de tabla e `INSERT IGNORE`.
- Módulo `DB/Conector.py` con conexión configurable por variables de entorno.
- Validador básico en `control/classes.py`.
- `.env.example`, `.gitignore` y documentación (`README.md`, `SECURITY.md`).

### Cambiado

- Conexión MySQL: host, usuario y nombre de BD configurables vía `DB_HOST`, `DB_USER`, `DB_NAME`.
- Dependencias: `mysql-connector-python` declarado en `requirements.txt`; eliminada dependencia no usada en el código actual.

### Corregido

- Uso correcto de `raise Exception(...)` en `control/classes.py`.
- Import explícito `from modules.repo import Repo` en `GH/GH.py`.

Repositorio: https://github.com/GustavoHunterN/GHdotcom
