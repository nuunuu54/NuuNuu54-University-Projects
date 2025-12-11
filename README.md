
# Setup-FabrikamServer — Extended User & Developer Guide

## Overview
`Setup-FabrikamServer-Extended.ps1` builds on the base script to add parameter validation, WSUS support, role-specific post-configuration (IIS default page & firewall, DNS zones & records), an answer-file mode, and controls to skip updates or suppress reboot.

---

## Prerequisites
- **OS:** Windows Server 2022 (Standard/Datacenter)
- **PowerShell:** 5.1 and 7+
- **Admin Rights:** Run as Administrator
- **Network:** Ensure IP/prefix/gateway/DNS values are valid for your subnet
- **Execution Policy:** `RemoteSigned` recommended

---

## New Parameters & Behaviors

- `-CreateDefaultIISPage` *(switch)*: Creates a simple `index.html` in `C:\inetpub\wwwroot`.
- `-EnableWebFirewallRules` *(switch)*: Enables common inbound firewall rules for HTTP/HTTPS.
- `-DnsZoneName` *(string)*: Creates a primary zone if not present (e.g., `corp.fabrikam.local`).
- `-DnsRecords` *(hashtable[])*: A records to add, e.g. `@(@{Name='www';IPv4='10.0.0.50'})`.
- `-UseWSUS` *(switch)* and `-WSUSServer` *(string)*: Use managed source; if a URL is provided, the script sets policy keys and restarts `wuauserv`.
- `-SkipUpdates` *(switch)*: Skips Windows Update step.
- `-NoReboot` *(switch)*: Suppresses automatic reboot; logs pending reboot only.
- `-ConfigPath` *(string)*: JSON or CSV answer file to pre-fill parameters.
- `-LogDirectory` *(string)*: Specifies a custom directory for log files. Defaults to `C:\Logs`.

### Answer File Formats

**JSON (single object):**
```json
{
  "Hostname": "FAB-WEB01",
  "IpAddress": "10.10.1.50",
  "SubnetMask": "255.255.255.0",
  "DefaultGateway": "10.10.1.1",
  "DnsServers": ["10.10.1.10", "10.10.1.11"],
  "Roles": ["Web-Server"],
  "CreateDefaultIISPage": true,
  "EnableWebFirewallRules": true,
  "TimeZone": "UTC"
}
```

**CSV (first row used):**
```csv
Hostname,IpAddress,SubnetMask,DefaultGateway,DnsServers,Roles,TimeZone
FAB-WEB01,10.10.1.50,255.255.255.0,10.10.1.1,"10.10.1.10|10.10.1.11","Web-Server",UTC
```
> Note: For multiple DNS servers in CSV, use a delimiter like `|` and map to an array after import if needed.

---

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

