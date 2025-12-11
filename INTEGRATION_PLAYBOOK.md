Integration Test Playbook — Fabrikam Server Setup (Extended)

Purpose

Step-by-step instructions to run an end-to-end integration test in a lab (Hyper-V or VMware) and capture screenshots and logs for evidence.

Prerequisites

- Two Windows Server 2022 VMs (one to configure — the "target", one as a client/test machine).
- Administrator access to both VMs.
- Network connectivity between client and target.
- The repository cloned on the target VM (or accessible via shared folder).
- PowerShell (5.1 or 7+) on the target VM.

Overview

1. Prepare target VM
2. Run script with parameters or answer-file
3. Verify services (IIS/DNS) from client VM
4. Capture screenshots and collect logs
5. Save artifacts into `screenshots/` and commit

Detailed Steps

1) Prepare the target VM

- Copy the repository to the target VM and open an elevated PowerShell prompt (Run as Administrator).
- Set execution policy if needed:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process -Force
```

- (Optional) Create a JSON answer file `server-config.json` near the script, example:

```json
{
  "Hostname": "FAB-INT-01",
  "IpAddress": "10.0.0.50",
  "SubnetMask": "255.255.255.0",
  "DefaultGateway": "10.0.0.1",
  "DnsServers": ["10.0.0.1"],
  "Roles": ["Web-Server"],
  "CreateDefaultIISPage": true,
  "EnableWebFirewallRules": true,
  "TimeZone": "UTC"
}
```

2) Run the script (target VM)

- Run with answer file (preferred):

```powershell
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\server-config.json -LogDirectory C:\Logs
```

- Or run with explicit parameters:

```powershell
.\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-INT-01 -IpAddress 10.0.0.50 -SubnetMask 255.255.255.0 -DefaultGateway 10.0.0.1 -DnsServers 10.0.0.1 -Roles Web-Server -CreateDefaultIISPage -EnableWebFirewallRules -LogDirectory C:\Logs
```

- While the script runs, it will produce a timestamped log in `C:\Logs` and a transcript file. Note the exact log filename printed in console or read the newest file in the directory.

3) Verify services from client VM

- From the client VM, test the IIS page:

```powershell
Invoke-WebRequest -Uri http://10.0.0.50 -UseBasicParsing -OutFile .\iistest.html
Get-Content .\iistest.html | Select-Object -First 20
```

- Test DNS resolution (if DNS role installed):

```powershell
Resolve-DnsName -Name www.corp.fabrikam.local -Server 10.0.0.50
```

4) Capture screenshots and artifacts (target VM)

- Capture the IIS page in a browser on the client or target VM and save as `screenshots/IIS_default_page.png`.

- Capture the DNS resolution output and save as `screenshots/DNS_record_resolution.png` (or copy the PowerShell output to a file and save a screenshot).

- Retrieve WSUS registry keys (if WSUS used) and save to file:

```powershell
Get-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate' | Out-File .\screenshots\WSUS_registry_keys.txt
Get-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU' | Out-File .\screenshots\WSUS_AU_registry_keys.txt
```

- Copy the active log and transcript into `screenshots/`:

```powershell
$latestLog = Get-ChildItem -Path C:\Logs -Filter 'ServerSetup_*.log' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $latestLog.FullName -Destination .\screenshots\
$latestTrans = Get-ChildItem -Path C:\Logs -Filter 'ServerSetup_*.transcript.txt' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $latestTrans.FullName -Destination .\screenshots\
```

- Optional: capture screenshot programmatically (PowerShell 5.1):

```powershell
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(0,0,0,0,$bmp.Size)
$bmp.Save(".\screenshots\screenshot_full.png", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
```

5) Collect Pester and CI evidence

- Copy the `Test_Results.txt` and any Pester output into `screenshots/`.
- If you ran the GitHub Actions CI, download the artifact and save a screenshot of the workflow run page as `screenshots/CI_results.png`.

6) Commit artifacts

```powershell
git add screenshots/*
git commit -m "Add integration run artifacts"
git push
```

Notes & cleanup

- If the run encountered an error, check `C:\Logs\ServerSetup_*.log` and the transcript to diagnose. The script will attempt to rollback registered changes on fatal error; validate rollback results.
- For repeated runs, consider creating a snapshot/restore point for the target VM to quickly revert state.
