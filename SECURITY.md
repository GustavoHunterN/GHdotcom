# Política de seguridad

## Credenciales

Este proyecto usa variables de entorno para tokens y contraseñas. El archivo `.env` **no debe** versionarse ni compartirse.

## Si se filtró un secreto

1. **GitHub:** revoca el token en [Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) y crea uno nuevo si lo necesitas.
2. **MySQL:** cambia la contraseña del usuario afectado y actualiza tu `.env` local.

## Reportar vulnerabilidades

Si encuentras un problema de seguridad en este repositorio, abre un issue privado o contacta al mantenedor por los canales que prefieras. No publiques detalles explotables en issues públicos hasta tener un acuerdo sobre divulgación.
