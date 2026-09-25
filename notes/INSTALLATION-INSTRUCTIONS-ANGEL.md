# LocalAI-Angel Installation & Operations Guide

This guide documents the **LocalAI-Angel** installation used by this repository.

LocalAI-Angel is not installed exactly like the original upstream LocalAI project. This build includes **Angel Nexus**, a Docker-based companion service, a LocalAI same-origin API proxy, custom web assets, and simple Windows start/stop/diagnostic launchers.

For the full upstream LocalAI documentation, see the official LocalAI project:
https://github.com/mudler/LocalAI

---

## 1. What Is Different From Standard LocalAI?

LocalAI-Angel adds:

- **Angel Nexus** module-management service
- Angel Nexus web interface inside the LocalAI workspace
- GitHub/community module discovery
- Module inspection and installation
- Repository registration
- Docker Compose integration for Nexus
- LocalAI → Angel Nexus same-origin API proxy
- Persistent Nexus data
- Custom Angel branding
- Windows easy-start and easy-stop launchers
- Windows diagnostic tooling
- A local workspace shared with the Nexus service

The normal LocalAI API remains available on:

```text
http://localhost:8080
```

Angel Nexus runs directly on:

```text
http://localhost:8877
```

The main user interface is:

```text
http://localhost:8080/app/angel-nexus
```

The Angel Nexus UI normally communicates through the LocalAI same-origin proxy:

```text
http://localhost:8080/api/angel-nexus
```

This avoids requiring the browser to make a direct cross-origin connection to port 8877.

---

# 2. Requirements

## Windows

Recommended:

- Windows 10/11
- Docker Desktop
- Git
- GitHub CLI (`gh`) — optional, but useful for repository management
- PowerShell

Docker Desktop must be running before starting LocalAI-Angel.

Check Docker:

```powershell
docker version
docker compose version
```

Check Git:

```powershell
git --version
```

Check GitHub CLI:

```powershell
gh --version
```

GitHub CLI is optional for running the application.

---

# 3. Repository Location

The working repository used by this installation is:

```text
C:\LocalAI-Angel
```

If you clone the project somewhere else, the launchers and commands should be run from that location.

Example:

```powershell
cd C:\LocalAI-Angel
```

---

# 4. First-Time Docker Startup

Make sure Docker Desktop is running.

From the repository directory:

```powershell
cd C:\LocalAI-Angel
```

Build the LocalAI-Angel images:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml build
```

Start the services:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml up -d --force-recreate
```

Check the containers:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml ps
```

Expected services include:

```text
angel-nexus-service
localai-angel-api-1
```

---

# 5. Easy Start

This project includes:

```text
START_ANGEL.bat
```

Double-click:

```text
START_ANGEL.bat
```

The launcher is intended to make normal startup easier without requiring the full Docker Compose command every time.

Before using it:

1. Start Docker Desktop.
2. Wait for Docker Desktop to become ready.
3. Run `START_ANGEL.bat`.

If startup appears stuck, use the diagnostic launcher described below.

---

# 6. Easy Stop

This project includes:

```text
STOP_ANGEL.bat
```

Double-click:

```text
STOP_ANGEL.bat
```

This stops the LocalAI-Angel Docker services without deleting the project data.

Stopping the containers does **not** mean the project has been uninstalled.

---

# 7. Diagnostic Launcher

The project includes:

```text
DIAGNOSE_ANGEL.bat
```

Run it when:

- Docker Desktop has recently been restarted
- Angel does not appear to start correctly
- the web UI is unavailable
- Nexus is unavailable
- a module operation fails
- you want to verify the installation before troubleshooting

The diagnostic process checks the LocalAI-Angel environment and required files.

---

# 8. Verify LocalAI

After startup, test:

```powershell
Invoke-WebRequest http://localhost:8080/readyz
```

A healthy LocalAI response should return HTTP `200`.

You can also open:

```text
http://localhost:8080
```

---

# 9. Verify Angel Nexus

Test the Nexus service directly:

```powershell
Invoke-WebRequest http://localhost:8877/api/health
```

A healthy response should resemble:

```json
{
  "ok": true,
  "service": "angel-nexus",
  "version": "3.0"
}
```

Test the LocalAI proxy:

```powershell
Invoke-WebRequest http://localhost:8080/api/angel-nexus/api/health
```

The proxy should return the Angel Nexus health response.

---

# 10. Open Angel Nexus

Open:

```text
http://localhost:8080/app/angel-nexus
```

The Angel Nexus workspace provides the module-management interface.

Depending on the current catalog, you may see functions such as:

- Module Library
- Refresh Catalog
- Inspect Module
- Install
- Update
- Add Repository

---

# 11. Angel Nexus API

The Nexus service exposes its API directly on port 8877.

Examples:

```text
GET http://localhost:8877/api/health
GET http://localhost:8877/api/modules
```

The LocalAI application also exposes Nexus through the same-origin proxy:

```text
GET http://localhost:8080/api/angel-nexus/api/health
GET http://localhost:8080/api/angel-nexus/api/modules
```

The web interface uses the proxy rather than requiring direct browser access to port 8877.

---

# 12. Docker Architecture

The installation uses two primary services.

```text
                    Browser
                       |
                       v
              LocalAI Web UI
              localhost:8080
                       |
                       v
          Angel Nexus API Proxy
                       |
                       v
             Docker Network
                       |
                       v
          Angel Nexus Service
             localhost:8877
```

Docker Compose files:

```text
docker-compose.yaml
docker-compose.nexus.override.yaml
```

The Nexus override adds the Angel Nexus service to the LocalAI environment.

---

# 13. Persistent Nexus Data

Angel Nexus data is stored in:

```text
nexus-data\
```

The Docker configuration maps this directory into the Nexus container:

```text
./nexus-data:/data
```

This means Nexus data can persist when containers are recreated.

Do not delete `nexus-data` unless you intentionally want to remove the associated Nexus data.

---

# 14. Shared Workspace

The Nexus container also receives the repository workspace:

```text
./:/workspace
```

Inside the Nexus container:

```text
/workspace
```

is the LocalAI-Angel repository.

This allows Nexus module-management operations to work with the project workspace.

---

# 15. Installing a Community Module

Open:

```text
http://localhost:8080/app/angel-nexus
```

Use the Angel Nexus Module Library.

Typical workflow:

```text
Discover
   ↓
Inspect
   ↓
Install
   ↓
Refresh
```

For repositories that are not already in the catalog, use the repository-add workflow when available.

Example repository:

```text
https://github.com/example/project.git
```

Only install repositories you trust and understand.

---

# 16. Updating a Module

The Angel Nexus interface can expose an `Update` action for installed modules.

The interface uses the module state to determine whether the available action is:

```text
Install
```

or:

```text
Update
```

Refresh the module catalog before assuming an update is available.

---

# 17. GitHub Integration

The repository for this project is:

```text
https://github.com/tcdoverlord/LocalAI-Angel
```

GitHub CLI can be used from PowerShell.

Check authentication:

```powershell
gh auth status
```

View the repository:

```powershell
gh repo view tcdoverlord/LocalAI-Angel
```

---

# 18. Common Docker Commands

## View services

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml ps
```

## View logs

LocalAI:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs api
```

Nexus:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs nexus
```

Follow logs:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs -f
```

## Restart

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml restart
```

## Stop

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml down
```

## Rebuild

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml build
```

## Rebuild and recreate

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml build
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml up -d --force-recreate
```

---

# 19. If Docker Desktop Was Restarted

If Docker Desktop was closed or restarted, first make sure Docker is healthy:

```powershell
docker version
```

Then:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml ps
```

If the containers are stopped:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml up -d
```

If the installation needs to be rebuilt:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml build
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml up -d --force-recreate
```

---

# 20. Basic Troubleshooting

## LocalAI does not load

Check:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml ps
```

Then inspect:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs api
```

Test:

```powershell
Invoke-WebRequest http://localhost:8080/readyz
```

---

## Angel Nexus does not load

Check:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml ps
```

Then:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs nexus
```

Test:

```powershell
Invoke-WebRequest http://localhost:8877/api/health
```

---

## Angel Nexus works directly but not inside LocalAI

Test the proxy:

```powershell
Invoke-WebRequest http://localhost:8080/api/angel-nexus/api/health
```

If direct Nexus works but the proxy does not, inspect the LocalAI API container logs:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs api
```

The API proxy depends on the Docker service name:

```text
nexus
```

and the internal Nexus URL:

```text
http://nexus:8877
```

---

## Module installation returns an error

First verify the catalog:

```powershell
Invoke-WebRequest http://localhost:8080/api/angel-nexus/api/modules
```

Then inspect Nexus logs:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.nexus.override.yaml logs nexus
```

If the problem involves a repository, verify that the repository URL is correct and accessible.

---

# 21. Important Port Reference

| Service | Port | Purpose |
|---|---:|---|
| LocalAI | 8080 | Main API and web interface |
| Angel Nexus | 8877 | Nexus service/API |
| React development environment | 3000 | Development-only workflow when used |

Normal use should begin at:

```text
http://localhost:8080
```

and Angel Nexus is available at:

```text
http://localhost:8080/app/angel-nexus
```

---

# 22. Windows Launcher Files

The project includes simple Windows operational helpers:

```text
START_ANGEL.bat
STOP_ANGEL.bat
DIAGNOSE_ANGEL.bat
```

Additional launcher documentation/configuration may include:

```text
README-LAUNCHER.txt
LAUNCHER-INTEGRITY.json
```

The launchers are intended to reduce the amount of Docker and PowerShell knowledge required for normal operation.

Advanced Docker commands remain available for troubleshooting and development.

---

# 23. Safe Update Philosophy

When changing LocalAI-Angel:

1. Verify the current working state.
2. Make one controlled change.
3. Rebuild only what is necessary.
4. Start the services.
5. Test LocalAI.
6. Test Angel Nexus.
7. Test the affected feature.
8. Preserve a working state before making another major change.

The project follows four guiding principles:

### Wait

Do not make unnecessary changes before understanding the current state.

### Alignment

Changes should remain consistent with the architecture and intended behavior.

### Containment

Keep changes limited to the component being repaired or improved.

### Repair

When something breaks, preserve the working state and restore functionality before continuing development.

---

# 24. Backup and Recovery

Important project backups are kept outside normal source publication where appropriate.

The repository uses:

```text
notes\backups\
notes\bug_fixes\
```

for development history and recovery material.

Do not delete recovery material simply because the current build works.

The project also uses Git as a recovery mechanism.

Before a significant architectural change:

```powershell
git status
git log -5 --oneline
```

Create a checkpoint commit when appropriate.

---

# 25. Development vs. Normal Use

### Normal user workflow

```text
Start Docker Desktop
        ↓
START_ANGEL.bat
        ↓
Open LocalAI
        ↓
Open Angel Nexus
        ↓
Use Module Library
```

### Developer workflow

```text
PowerShell
   ↓
Git
   ↓
Docker Compose
   ↓
LocalAI
   ↓
Angel Nexus
   ↓
Logs / diagnostics / tests
```

---

# 26. Current Project Direction

LocalAI-Angel is being developed as a local-first AI workspace rather than a replacement for LocalAI itself.

Current and planned areas include:

- Community module management
- GitHub integration
- AI tools
- Local knowledge systems
- Knowledge provenance
- Grounding and retrieval
- Offline/local operation
- Docker-based services
- Additional Angel Nexus modules
- Improved diagnostics and recovery
- Future AI-assisted tool planning with controlled permissions

These areas are under active development and should not be interpreted as all being production-complete in the current alpha release.

---

# 27. Quick Start

For the normal Windows installation:

```text
1. Start Docker Desktop
2. Wait for Docker Desktop to become ready
3. Double-click START_ANGEL.bat
4. Open http://localhost:8080
5. Open http://localhost:8080/app/angel-nexus
```

To stop:

```text
Double-click STOP_ANGEL.bat
```

To diagnose:

```text
Double-click DIAGNOSE_ANGEL.bat
```

---

# 28. Project

GitHub:

https://github.com/tcdoverlord/LocalAI-Angel

Upstream LocalAI:

https://github.com/mudler/LocalAI

LocalAI-Angel is an evolving development project built on top of the LocalAI foundation.

> LocalAI provides the foundation.  
> Angel provides the experience.  
> Nexus provides the coordination.
