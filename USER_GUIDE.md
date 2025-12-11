Setup-FabrikamServer-Extended — User Guide

Overview

`Setup-FabrikamServer-Extended.ps1` automates baseline configuration for Windows Server (hostname, network, roles such as IIS/DNS), optional WSUS configuration, Windows Update orchestration, and post-install tasks.

Prerequisites

- Windows Server 2022 Evaluation or licensed install (ISO or image available).
- A hypervisor (Hyper-V or VMware) with at least 2 virtual servers for testing (one server to configure, one to act as a client/test resolver as needed).
- PowerShell: Windows PowerShell 5.1 or PowerShell 7+. When installing Windows Features, the script will call Windows PowerShell 5.1 if run under PS 7 to maintain compatibility.
- Script editing/debugging: PowerShell ISE or VS Code recommended.
- Run elevated (Administrator) session.
- Execution policy: `RemoteSigned` recommended.

Files in repo

- `Setup-FabrikamServer-Extended.ps1` — The main automation script.
- `Setup-FabrikamServer-Extended.Tests.ps1` — Pester tests for helper functions and answer-file parsing.
- `USER_GUIDE.md` — This file.
- `DEVELOPER_DOCS.md` — Developer documentation (function reference, design decisions).
- `FINAL_REPORT.md` — Final report mapping rubric requirements to repo deliverables.
- `Test_Results.txt` — Captured Pester test output (latest).

Quick start

1. Copy the script to the target server or network share.
2. Open an elevated PowerShell (Run as Administrator).
3. (Optional) If using an answer file, create a JSON or CSV with the parameters. JSON is preferred for complex arrays.
4. Run the script. Examples:

```powershell
# Using explicit parameters
.\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-WEB01 -IpAddress 10.10.1.50 -SubnetMask 255.255.255.0 \
  -DefaultGateway 10.10.1.1 -DnsServers 10.10.1.10,10.10.1.11 -Roles Web-Server -CreateDefaultIISPage -EnableWebFirewallRules

# Using a JSON answer file
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\server-config.json
```

Expected outputs

- Console logging of steps and progress.
- Persistent log files and transcript under `C:\Logs` by default: `ServerSetup_yyyyMMdd_HHmmss.log` and corresponding transcript.
- If `-NoReboot` not set, the script may reboot the server when required.

Testing the script locally (Pester)

1. Ensure `Pester` module is installed (PowerShell 5.1 often includes it; for newer versions install from PSGallery):

```powershell
Install-Module Pester -Scope CurrentUser -Force
```

2. Run the included tests:

```powershell
Invoke-Pester -Path .\Setup-FabrikamServer-Extended.Tests.ps1
```

The tests validate helper functions and the answer-file parsing logic.

Notes and best practices

- For repetitive/infrastructure deployments, consider converting the configuration to DSC or integrate with Windows Admin Center/automation tooling.
- Use JSON answer files for complex inputs (arrays, booleans) to avoid CSV parsing edge cases.
- Always test in an isolated environment before applying to production servers.

Dry-Run Mode

- **Purpose:** Use the `-DryRun` switch to preview actions the script would take without applying any changes. This is useful for validation and demonstrating the impact of the script in a safe manner.
- **Behavior:** When `-DryRun` is supplied the script will log planned actions (prefixed with `DRY-RUN:`) and skip operations that modify the system, such as renaming the computer, changing network settings, installing features, modifying WSUS registry keys, creating IIS files, or applying Windows updates.
- **Example:**

```powershell
# Preview actions from an answer file without making changes
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\server-config.json -DryRun

# Preview actions for a specific run
.\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-DRY -IpAddress 10.0.0.50 -SubnetMask 255.255.255.0 -DefaultGateway 10.0.0.1 -DnsServers 10.0.0.1 -Roles Web-Server -CreateDefaultIISPage -EnableWebFirewallRules -DryRun
```

After running with `-DryRun`, inspect the console output and the log (if writing to a log directory was not suppressed) for `DRY-RUN:` entries describing planned changes.
