# LocalAI Angel Unified v1.0.0 — Release Candidate

## Included stack

- LocalAI source build and original LocalAI web UI (`http://127.0.0.1:8080/app`)
- Angel AI Harness chat/workspace (`http://127.0.0.1:8765/`)
- Angel Nexus UI (`http://127.0.0.1:8080/app/angel-nexus`) and API (`http://127.0.0.1:8877`)
- Internal Ollama fallback with the configured `llama3.2:3b` default model
- Persistent Angel knowledge/history data and Nexus data

## Windows startup files

- `INSTALL_ANGEL_V1.0.0.bat` — first install or rebuild; builds images and starts all services.
- `RUN_ANGEL_V1.0.0.bat` — everyday startup; does not rebuild images.
- `STOP_ANGEL_V1.0.0.bat` — stops the Compose stack without deleting persistent data.
- `INSTALL_ANGEL_V1.0.0.ps1` — PowerShell installer with a transcript log.

Keep the three Compose files beside these scripts. Start Docker Desktop before running them.

## Data safety

The scripts use the same three-file Compose stack as the supplied working build. They never run `docker compose down -v`, `docker volume rm`, or a destructive cleanup command. An existing `.env` is preserved. Its `ANGEL_USER_DATA` value determines where Angel's persistent data is stored; check this value before moving the installation to another PC. Back up the configured data directory and `nexus-data` before publishing or upgrading.

## Release status

This package is a **v1.0.0 release candidate**, not a fully certified release. The supplied source ZIP has not been rebuilt or exercised on the user's Windows/Docker machine by this packaging step. After extraction, run the installer and verify all three endpoints, a real chat response, retrieved knowledge, conversation history after restart, and Nexus module persistence before tagging a public v1.0.0 release.
