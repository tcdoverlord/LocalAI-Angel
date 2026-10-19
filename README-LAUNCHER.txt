LOCALAI-ANGEL ONE-CLICK LAUNCHER
================================

INSTALL
1. Extract these files into the root of the LocalAI-Angel repository.
2. START_ANGEL.bat must sit beside docker-compose.yaml.
3. Double-select START_ANGEL.bat.

FILES
- START_ANGEL.bat starts Docker Desktop if needed, validates Compose,
  starts LocalAI plus Angel Nexus, checks both health endpoints, and
  opens the LocalAI interface.
- STOP_ANGEL.bat stops the services without removing containers,
  model storage, or Nexus data.
- DIAGNOSE_ANGEL.bat produces angel-diagnostics.txt and opens it.

EXPECTED REPOSITORY LAYOUT
LocalAI-Angel  START_ANGEL.bat
  STOP_ANGEL.bat
  DIAGNOSE_ANGEL.bat
  docker-compose.yaml
  docker-compose.nexus.override.yaml
  nexus-service  nexus-data
ENDPOINTS
- LocalAI: http://localhost:8080
- LocalAI readiness: http://localhost:8080/readyz
- Angel Nexus health: http://localhost:8877/api/health

NOTES
- Docker Desktop must be installed.
- The first build may take time.
- A running runtime and an installed AI model are separate states.
- STOP uses "docker compose stop", not "down", to preserve the stack.

RELIABILITY FIX
---------------
Critical prerequisite failures in START_ANGEL.bat now terminate the launcher
immediately after the fatal error handler returns. This prevents the script
from continuing into Docker startup after a missing prerequisite or failed
validation.


RELIABILITY FIX (READY PACKAGE)
START_ANGEL.bat uses parenthesized CMD IF blocks around prerequisite and error exits. This ensures goto :eof runs only when the corresponding check fails.


CONTAINER RECOVERY UPDATE
The launcher now checks for an existing container named angel-nexus-service
before Compose startup.

- If it is labeled as Compose project localai-angel and service nexus, it is kept.
- If it is missing, startup proceeds normally.
- If it exists but is stale/unrelated, only that conflicting container is removed.
- No Docker volumes, images, source files, or nexus-data are deleted.
- Compose startup uses `up -d` without forcing a rebuild.
- Docker/Compose output remains visible so startup failures are observable.


FINAL WORKING BASELINE
This launcher is based on the proven manual LocalAI-Angel startup sequence.
It checks the existing angel-nexus-service container before Compose startup,
keeps it when it belongs to project localai-angel/service nexus, and removes
only a stale/unrelated container with that exact conflicting name.

Startup uses docker compose up -d exactly once, without forcing a rebuild.
Docker Compose output remains visible. No volumes, models, nexus-data, source
files, or unrelated containers are deleted.
