Angel Nexus Service Scripts v0.6.0

Copy the six .ps1 files into:
D:\LocalAI-v1.0.0\scripts

Expected layout:
D:\LocalAI-v1.0.0\
  scripts\Start-LocalAI.ps1
  scripts\Stop-LocalAI.ps1
  scripts\Start-Nexus.ps1
  scripts\Stop-Nexus.ps1
  scripts\Start-React.ps1
  scripts\Stop-React.ps1

Defaults:
- LocalAI container: localai-v100-api-1
- LocalAI readiness: http://localhost:8080/readyz
- Nexus root: ..\nexus-service
- Nexus health: http://localhost:8877/api/health
- React root: ..\core\http\react-ui
- React health: http://localhost:3000

Review the container name and paths before running.
Run from an elevated or normal PowerShell session as appropriate:
Set-ExecutionPolicy -Scope Process Bypass
