
﻿# Server-Admin-Project — Windows Server automation

<div align="center">

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

</div>

## Overview

`Setup-FabrikamServer-Extended.ps1` automates baseline configuration for Windows Server
including hostname, static networking, Windows feature installation (IIS/DNS), WSUS
policy configuration, Windows Update orchestration, and post-install tasks. The script
includes a dry-run preview mode and a rollback framework to safely undo applied changes.

This branch contains the PowerShell automation, tests, and documentation. For the IDS
project (separate), see the `IDS-Project` branch.

## Key Features

- Parameter validation and answer-file support (JSON / CSV)
- Dry-run mode (`-DryRun`) — shows planned actions without applying changes
- Rollback framework — registers reversible actions and rolls back on error
- Cross-version compatibility (PowerShell 5.1 and PowerShell 7+)
- Role-specific post-install configuration: IIS default page, DNS zone/records
- WSUS registry configuration and Windows Update orchestration
- Pester test suite for helper functions and parsing logic

## Quick Start

Prerequisites:
- Windows Server 2022
- Run PowerShell as Administrator
- Execution policy: `RemoteSigned` recommended

Clone and use Server-Admin-Project branch:

```powershell
git clone https://github.com/nuunuu54/NuuNuu54-University-Projects.git
cd "Server-Admin-Work"
git checkout Server-Admin-Project
```

Preview what the script would do (recommended):

```powershell
.\Setup-FabrikamServer-Extended.ps1 -DryRun -ConfigPath .\test-config.json -SkipUpdates
```

To apply changes, run without `-DryRun`:

```powershell
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\test-config.json
```

## Installation & Tests

This project uses Pester for unit tests and GitHub Actions for CI. To run tests locally:

```powershell
Install-Module Pester -Scope CurrentUser -Force
Invoke-Pester -Path .\Setup-FabrikamServer-Extended.Tests.ps1
```

Test results are included in `Test_Results.txt` (excerpt below).

## Example Dry-Run Output (excerpt)

Below is a short excerpt from the dry-run demonstration (`DRY_RUN_OUTPUT.md`). It
shows how the script logs planned changes with the `DRY-RUN:` prefix.

```
[2025-12-11 12:45:31] [INFO] DRY-RUN: Rename computer to FAB-SERVER01
[2025-12-11 12:45:33] [INFO] DRY-RUN: Set static IP: 192.168.1.100/24
[2025-12-11 12:45:34] [INFO] DRY-RUN: Install Windows feature: Web-Server
[2025-12-11 12:45:35] [INFO] DRY-RUN: Create default IIS page at C:\\inetpub\\wwwroot\\index.html
[2025-12-11 12:45:37] [INFO] DRY-RUN: Set registry key HKLM\\\\Software\\\\Policies\\\\Microsoft\\\\Windows\\\\WindowsUpdate\\\\AU
[2025-12-11 12:45:38] [INFO] DRY-RUN MODE: No actual changes applied
```

Full dry-run output and guidance are in `DRY_RUN_OUTPUT.md`.

## Test Output (Pester) — excerpt

```
Describing Setup-FabrikamServer-Extended Function Tests
  Context Convert-SubnetMaskToPrefixLength
    [+] should convert a valid subnet mask to a prefix length
    [+] should throw an error for an invalid subnet mask
  Context Test-IPv4Address
    [+] should return true for a valid IPv4 address
    [+] should return false for an invalid IPv4 address
  Context Get-PrimaryInterface
    [+] should return the first "Up" interface
  Context Import-AnswerFile
    [+] should import a JSON answer file

Tests completed in 00:00:15.27
Passed: 12 Failed: 0 Skipped: 0
```

See `Test_Results.txt` for the full output.

## Documentation

- `USER_GUIDE.md` — User instructions and examples
- `DEVELOPER_DOCS.md` — Developer reference and architecture
- `INTEGRATION_PLAYBOOK.md` — Lab testing/verification steps
- `DRY_RUN_OUTPUT.md` — Complete dry-run demonstration
- `COMPLETENESS_CHECKLIST.md` — Project validation checklist

## Contributing & CI

Contributions: open a pull request against `Server-Admin-Project`. CI runs Pester
tests and PSScriptAnalyzer on push/PRs.

## License

MIT — see repository for details.

## Usage Examples

```powershell
# IIS with default homepage + firewall
.\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-WEB01 -IpAddress 10.10.1.50 -SubnetMask 255.255.255.0 `
  -DefaultGateway 10.10.1.1 -DnsServers 10.10.1.10,10.10.1.11 -Roles Web-Server -CreateDefaultIISPage -EnableWebFirewallRules

# DNS with zone and records
.\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-DNS01 -Roles DNS -DnsZoneName corp.fabrikam.local `
  -DnsRecords @(@{Name='www';IPv4='10.0.0.50'},@{Name='api';IPv4='10.0.0.60'})

# Use WSUS; skip reboot
.\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-SRV22 -UseWSUS -WSUSServer http://wsus.fabrikam.local -NoReboot

# Answer file
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\server.json
```

---

## Expected Output & Logs
- **Log:** `C:\Logs\ServerSetup_yyyyMMdd_HHmmss.log`
- **Transcript:** `C:\Logs\ServerSetup_yyyyMMdd_HHmmss.transcript.txt`
- **Reboot:** Automatic unless `-NoReboot` is used

---

## Test Plan Additions
- Verify IIS default page reachable (`http://<server>`), firewall rules enabled.
- Verify DNS zone exists: `Get-DnsServerZone -Name <zone>`; records resolve: `Resolve-DnsName www.<zone>`.
- Verify WSUS policy keys under `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` and service restart.
- Answer file: Confirm parameters are pre-filled when not provided on the command line.

---

## Troubleshooting Additions
- **WSUS not applying:** Ensure proper URL (`http://server:port`). Confirm `UseWUServer=1` under policy and that `wuauserv` restarted.
- **IIS page not created:** Confirm `-CreateDefaultIISPage` used and write permissions to `C:\inetpub\wwwroot`.
- **DNS module not found:** Ensure `DNS` role installed; reopen elevated PowerShell if module import fails.

---

## Deliverables (current repo)

- `Setup-FabrikamServer-Extended.ps1` — main automation script (modular, commented).
- `Setup-FabrikamServer-Extended.Tests.ps1` — Pester tests for helper functions and CSV/JSON answer file parsing.
- `USER_GUIDE.md` — user instructions and quick-start (added).
- `DEVELOPER_DOCS.md` — developer-focused documentation and function reference (added).
- `FINAL_REPORT.md` — mapping of rubric to repo and actions taken (added).
- `Test_Results.txt` — Pester results / logs (updated).

If anything else is desired (CI pipeline, screenshots, or a PR), tell me which next and I will prepare it.

CI
-- A GitHub Actions workflow has been added at `.github/workflows/ci.yml`. It runs on Windows, installs `Pester` and `PSScriptAnalyzer`, runs script analysis, executes the Pester tests, and uploads `Test_Results.txt` as an artifact.

Screenshots
-- A `screenshots/` folder was added with guidance (`screenshots/README.md`) and a `sample_log.txt` placeholder. Please add real PNG screenshots from your lab into this folder (IIS page, DNS resolution, WSUS registry keys, logs listing, Pester/CI results).

