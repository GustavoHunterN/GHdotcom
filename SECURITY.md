# Security policy

## Credentials

This project uses environment variables for tokens and passwords. The `.env` file **must not** be committed or shared.

## If a secret was exposed

1. **GitHub:** Revoke the token under [Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) and create a new one if needed.
2. **MySQL:** Change the affected user password and update your local `.env`.

## Reporting issues

If you find a security problem in this repository, contact the maintainer privately or use GitHub’s reporting options. Do not post exploitable details in public issues before coordinated disclosure.
