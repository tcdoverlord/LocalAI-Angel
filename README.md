<div align="center">
  <img src="./core/http/static/logo.png" alt="LocalAI-Angel logo" width="150">

  # LocalAI-Angel

  **A ready-to-use Angel AI experience, backed by LocalAI and expanded by Angel Nexus.**

  [![Open Source](https://img.shields.io/badge/Open%20Source-Explore%20the%20Code-58a6ff?style=for-the-badge)](https://github.com/tcdoverlord/LocalAI-Angel)
  [![LocalAI](https://img.shields.io/badge/Powered%20by-LocalAI-55d6a0?style=for-the-badge)](https://localai.io/)

  [Get Started](#quick-start) · [Angel AI](#angel-ai-the-easy-start) · [Platform Overview](#three-connected-layers) · [Issues](https://github.com/tcdoverlord/LocalAI-Angel/issues)
</div>

---

> **The idea:** start with an AI assistant you can use, then grow into a more capable platform. Angel AI is the welcoming front door; LocalAI provides the model/inference layer; Angel Nexus is the modular tools and integration layer.

## Angel AI: the easy start

The project includes an Angel AI starter experience intended to let you begin chatting without first assembling the entire AI stack yourself.

**Internet required:** the ready-to-use starter uses an internet-connected AI service/model path and is intended to work at no cost under the provider's available free access. Provider limits, account requirements, and terms may change. This is **not** the same as fully offline AI.

If you want to explore local inference, LocalAI supports running compatible models on your own system. Local model use depends on your hardware, model choice, and configuration.

## Three connected layers

| Component | Role |
|---|---|
| **Angel AI** | The approachable assistant experience and starting point for everyday AI use. |
| **LocalAI** | The model and inference layer for supported local models, services, and APIs. |
| **Angel Nexus** | A modular platform for tools, integrations, and future extensions. |

## What this project is working toward

- A starter experience that is easier to launch than a from-scratch AI setup.
- A modular architecture that keeps the assistant, inference service, and integrations distinct.
- Persistent assistant features such as chat history, summaries, knowledge retrieval, and project context.
- A path to local models and expanded AI capabilities.
- Tool use with clear approval boundaries and verification.
- A foundation for experimentation and future modules.

Some capabilities may be experimental, hardware-dependent, or still in development. The repository and its current docs are the source of truth for what is available in a particular build.

## Quick start

1. Review the prerequisites and launch notes in the repository.
2. Start Docker Desktop if required by the supplied launcher.
3. From the project folder, run the unified starter launcher documented for the current build: `START_ANGEL_UNIFIED.bat`.
4. Follow the launcher's output and current documentation to open Angel Home Base, LocalAI, and Nexus where available.

**Before launching:** check the repository's current docs and example environment file for prerequisites, model/provider configuration, ports, and troubleshooting. Never commit real API keys, tokens, or private `.env` files.

### Choose your path

- **Connected starter:** internet required; free access depends on the configured provider's current limits and terms.
- **Local models:** can reduce reliance on hosted inference, but require compatible models and local compute. They may require additional setup.

## Project links

- [Browse the repository](https://github.com/tcdoverlord/LocalAI-Angel)
- [Angel AI Harness](https://github.com/tcdoverlord/LocalAI-Angel/tree/main/Angel_AI_Harness)
- [LocalAI documentation](https://localai.io/)
- [Report an issue](https://github.com/tcdoverlord/LocalAI-Angel/issues)
- [Pull requests](https://github.com/tcdoverlord/LocalAI-Angel/pulls)

## License and attribution

This repository integrates upstream LocalAI with the Angel project. Review the license files and attribution notices for this repository and its individual components before redistributing. Do not assume every upstream component has the same license.

---

<div align="center"><sub>Built by <a href="https://github.com/tcdoverlord">TCDOVERLORD</a> · LocalAI-Angel</sub></div>
