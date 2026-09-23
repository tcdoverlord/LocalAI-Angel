# Angel Nexus Contribution Build

This build preserves the existing LocalAI source and adds an initial, safe-by-default
Angel Nexus Change Control layer.

## Contributions included

1. **Patch/Change Control foundation**
   - Standard JSON patch manifests
   - Exact-match edits (must match exactly once)
   - Target-root path protection
   - Dated Git safe-point records
   - Trusted validation profiles
   - Automatic rollback on failure
   - Append-only patch ledger

2. **GitHub Module area foundation**
   - Preserves the existing Angel Nexus GitHub module UI/service
   - Adds a standard place for module patches and future module lifecycle work
   - Does not replace LocalAI's existing application architecture

## Quick start on Windows

From the LocalAI repository root:

```powershell
.\tools\angel-nexus\AngelNexus-Patch.ps1 `
  -Action validate `
  -Patch .\tools\angel-nexus\patches\example.patch.json

.\tools\angel-nexus\AngelNexus-Patch.ps1 `
  -Action apply `
  -Patch .\tools\angel-nexus\patches\example.patch.json `
  -TargetRoot .
```

The example patch is illustrative and targets a placeholder path; create a real patch
manifest for a real file before applying it.

## Safety model

- The engine never accepts arbitrary shell commands from a patch manifest.
- Validation profiles are selected from a trusted server-side allow-list.
- The engine refuses absolute paths and `..` traversal.
- A patch is not marked accepted merely because file edits succeeded.
- A failed validation causes rollback to the safe point.
- The target Git worktree must be clean before a safe point is created; this prevents rollback from deleting unrelated uncommitted work.
- Review and commit remain separate from patch execution.

## Current limitations

This is the first integration foundation, not a finished upstream-ready PR:
- The existing sidecar service still needs authentication and authorization before
  exposing write operations beyond a trusted local development environment.
- The UI has not yet been wired to every patch endpoint.
- Full LocalAI CI and platform-specific integration tests must run in the target
  development environment.
