# LocalAI-Angel Unified 0.3.0 — Harness-integrated home base

**This is the integrated build, not the earlier placeholder chat runtime.** It keeps the LocalAI-Angel source build (including its Nexus route), launches the existing Angel Nexus repository/module runner, and runs the Angel AI Harness workspace as the main assistant experience.

## Architecture

- **LocalAI fork (`api`)** — inference engine, model gallery, OpenAI-compatible `/v1/chat/completions` API, and the custom React UI containing the Angel Nexus page.
- **Angel Nexus (`nexus`)** — existing repository/module catalog and controlled prepare/run workflows through LocalAI's `/api/angel-nexus/*` proxy.
- **Angel AI Harness (`angel-harness`)** — established chat runtime/UI, SQLite conversation store and summaries, local date/time route, provider-backed current/tomorrow weather, knowledge retrieval and evidence/confidence routes, projects, skills/capabilities, read-aloud, and approval-gated actions.
- **Provider adapter** — uses LocalAI's `http://api:8080/v1/models` and `/v1/chat/completions` by default. Optional Ollama fallback is available through a profile; LocalAI remains the preferred provider; a persistent Ollama sidecar provisions the default Angel model automatically and is used when LocalAI has no chat model.
- **Built-in K–12 starter pack** — an original, expandable set of general K–12 learning references seeded into the user's knowledge packs the first time the Harness runtime starts. It is a starter reference, not a complete set of official state standards or a full curriculum database.

```text
Browser
  ├── Angel Home Base (Harness UI) http://127.0.0.1:8765
  │     ├── chat + SQLite history/summaries
  │     ├── deterministic date/time and weather routes
  │     ├── knowledge/retrieval/EBR + K–12 starter pack
  │     └── LocalAI model selector + links to LocalAI and Nexus
  └── LocalAI React UI http://127.0.0.1:8080
        ├── model gallery / inference API
        └── /app/angel-nexus — Nexus module/repository manager
```

## First launch on Windows

1. Extract this repository into a new folder, for example `D:\LocalAI-Angel-Unified`.
2. Start Docker Desktop and wait until its Linux engine is running.
3. Close the standalone Angel Harness app before launch if it is using the same `C:\Users\<you>\Angel_Platform` data directory.
4. Run `START_ANGEL_UNIFIED.bat`.
5. The first LocalAI source build can take a long time and needs substantial free disk space. The launcher builds the **fork source** (rather than substituting the unmodified upstream image), so the Nexus routes built into this tree are preserved.
6. Open Angel at `http://127.0.0.1:8765`. LocalAI model management is at `http://127.0.0.1:8080`, and Nexus is at `http://127.0.0.1:8080/app/angel-nexus`.
7. On first launch, the model-init service downloads `qwen2.5:3b` into the persistent Ollama model volume. This download is not bundled in the source ZIP and can take several minutes. Angel uses it automatically when LocalAI has no chat model. LocalAI's own model gallery remains available for installing additional LLMs; when LocalAI has a model, LocalAI stays the preferred provider. Deterministic date/time, live weather, and knowledge retrieval do not require a language model, but free-form reasoning does.

## Persistent data and past chats

By default, the Windows launcher bind-mounts the existing `C:\Users\<you>\Angel_Platform` folder into `/data` in the Harness container. The Harness `ANGEL_DATA_DIR` setting makes the web runtime, SQLite database, summaries, knowledge library, snapshots, activity records, and related files use that same persistent directory. This is meant to **reuse rather than overwrite** the previously working Harness data.

Before the first launch, make a copy of `C:\Users\<you>\Angel_Platform` and stop any standalone Harness process that is writing to it. Existing database content is not replaced by the startup script. The source's knowledge seeding copies `angel-k12-core` only if that pack folder does not already exist; it never overwrites an existing user-edited copy.

If you do not have an existing `Angel_Platform` folder, the launcher creates it. For non-Windows/manual Compose startup, set `ANGEL_USER_DATA` to a persistent writable host path or use the default `./Angel_Platform_Data` directory.

## Built-in default model and additional LLMs

The default build starts a persistent Ollama sidecar and automatically downloads `qwen2.5:3b` on first launch. The model weights are stored in the `ollama-models` Docker volume, not inside the source ZIP. Angel uses LocalAI first whenever LocalAI has a chat model; if LocalAI has no model, Angel falls back to the provisioned default. Users can install additional LLMs through LocalAI's model gallery without losing Angel's identity, conversation history, or knowledge. Ollama's default model is separate from LocalAI's model gallery and is not automatically copied into LocalAI.

## Time, weather, and timezone

The Harness routes date/time requests using the container's local time zone and weather requests through its existing Open-Meteo lookup code. `ANGEL_TIMEZONE` defaults to `America/Indiana/Indianapolis`; change it in `.env` when deploying in another time zone. Weather requires internet access; if provider calls fail the assistant reports the failure instead of inventing live conditions.

## Repository initialization

This folder is designed to become a separate repository. After reviewing the source/license notices:

```powershell
git init
git add .
git commit -m "Create LocalAI-Angel Unified Harness integration"
```

Do not commit `.env`, the `Angel_Platform` user data folder, downloaded model weights, or runtime repository clones. The included `.gitignore` covers common local data. The LocalAI Dockerfile is adjusted so a clean source archive can build without requiring a nested `.git` folder in the Docker context; its build version falls back safely when Git metadata isn't available.

## Validation scope

Static integration tests verify Harness syntax, weather-route behavior, first-run K–12 seeding, provider model discovery/stream parsing with mocked HTTP responses, and the Compose structure. The full LocalAI source image build, Docker engine startup, hardware-specific inference performance, and live weather API calls must be validated on the target computer. The default model weights are downloaded on first launch rather than bundled in the source ZIP; user hardware and chosen model affect response speed. The complete container startup and live inference must still be confirmed on the target computer.

## Upstream and attribution

The project includes source from LocalAI-Angel and Angel-AI-Harness. Preserve their original license and attribution files (`LICENSE` and `Angel_AI_Harness/LICENSE.md`) when redistributing. This integration does not imply that every advanced Harness action has been connected to Nexus; existing features remain within their original routes until explicitly wired and tested.
