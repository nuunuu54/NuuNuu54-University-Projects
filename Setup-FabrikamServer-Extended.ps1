
<#
.SYNOPSIS
    Fabrikam Server Automation — Extended: Baseline configuration, networking, roles (IIS/DNS), Windows Updates, WSUS, and post-config tasks.

.DESCRIPTION
    Setup-FabrikamServer-Extended.ps1 enhances the original automation by adding:
      - Robust IPv4/DNS parameter validation.
      - Configurable WSUS support (optional registry policy update).
      - Role-specific post-configuration:
          * IIS: optional default homepage, firewall rule enablement.
          * DNS: optional zone creation and A records.
      - Answer file support via -ConfigPath (JSON or CSV) to pre-fill parameters.
      - Optional flags to skip updates or suppress automatic reboot.

    Compatible with Windows PowerShell 5.1 and PowerShell 7+.
    For role installation in PowerShell 7+, it invokes Windows PowerShell (ServerManager) in a separate process.

.PARAMETER Hostname
    The desired computer name.

.PARAMETER IpAddress
    The IPv4 address to assign to the primary NIC.

.PARAMETER PrefixLength
    CIDR prefix length (1–32). If omitted and SubnetMask is provided, it will be derived.

.PARAMETER SubnetMask
    Dotted IPv4 mask (e.g., 255.255.255.0). Used to derive PrefixLength.

.PARAMETER DefaultGateway
    IPv4 default gateway.

.PARAMETER DnsServers
    One or more IPv4 DNS servers.

.PARAMETER Roles
    Approved roles to install. Valid: 'Web-Server','DNS'. Defaults to both.

.PARAMETER TimeZone
    Windows time zone ID (e.g., 'UTC','Pacific Standard Time').

.PARAMETER InterfaceAlias
    Network adapter alias. If omitted, the first 'Up' adapter is selected.

.PARAMETER CreateDefaultIISPage
    Switch to generate a default index.html in the site root after IIS installation. Default: On.

.PARAMETER EnableWebFirewallRules
    Switch to enable common inbound firewall rules for HTTP/HTTPS after IIS installation. Default: On.

.PARAMETER DnsZoneName
    If provided, creates a primary DNS zone with this name (e.g., 'corp.fabrikam.local').

.PARAMETER DnsRecords
    Optional array of hashtables to create A records, e.g., @(@{Name='www';IPv4='10.0.0.50'})

.PARAMETER UseWSUS
    Switch to use a managed update source. If -WSUSServer is provided, configures policy to point to it.

.PARAMETER WSUSServer
    WSUS server URL (e.g., 'http://wsus.fabrikam.local'). When specified with -UseWSUS, sets policy keys and restarts wuauserv.

.PARAMETER SkipUpdates
    Switch to skip Windows Update step.

.PARAMETER NoReboot
    Switch to suppress automatic reboot; pending reboot will be logged only.

.PARAMETER ConfigPath
    Path to a JSON or CSV answer file to pre-fill parameters. JSON should be an object with keys matching parameters.
    CSV should contain a single row or the script will pick the first row.

.EXAMPLE
    # Full setup with static IP, IIS only, default homepage and firewall rules
    .\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-WEB01 -IpAddress 10.10.1.50 -SubnetMask 255.255.255.0 `
      -DefaultGateway 10.10.1.1 -DnsServers 10.10.1.10,10.10.1.11 -Roles Web-Server -CreateDefaultIISPage -EnableWebFirewallRules

.EXAMPLE
    # DNS server with zone and records
    .\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-DNS01 -Roles DNS -DnsZoneName corp.fabrikam.local `
      -DnsRecords @(@{Name='www';IPv4='10.0.0.50'},@{Name='api';IPv4='10.0.0.60'})

.EXAMPLE
    # Use WSUS for updates and suppress reboot
    .\Setup-FabrikamServer-Extended.ps1 -Hostname FAB-SRV22 -UseWSUS -WSUSServer http://wsus.fabrikam.local -NoReboot

.EXAMPLE
    # Answer file (JSON) to pre-fill parameters
    .\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\server.json

.NOTES
    Author: Fabrikam IT Automation (Senior Engineer)
    Logging: C:\Logs\ServerSetup_yyyyMMdd_HHmmss.log
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Hostname,

    [Parameter(Mandatory = $false)]
    [string]$IpAddress,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1,32)]
    [int]$PrefixLength,

    [Parameter(Mandatory = $false)]
    [string]$SubnetMask,

    [Parameter(Mandatory = $false)]
    [string]$DefaultGateway,

    [Parameter(Mandatory = $false)]
    [string[]]$DnsServers,

    [Parameter(Mandatory = $false)]
    [ValidateSet('Web-Server', 'DNS')]
    [string[]]$Roles = @('Web-Server','DNS'),

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$TimeZone = 'UTC',

    [Parameter(Mandatory = $false)]
    [string]$InterfaceAlias,

    [Parameter(Mandatory = $false)]
    [bool]$CreateDefaultIISPage = $true,

    [Parameter(Mandatory = $false)]
    [bool]$EnableWebFirewallRules = $true,

    [Parameter(Mandatory = $false)]
    [ValidatePattern('^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')]
    [string]$DnsZoneName,

    [Parameter(Mandatory = $false)]
    [hashtable[]]$DnsRecords,

    [Parameter(Mandatory = $false)]
    [switch]$UseWSUS,

    [Parameter(Mandatory = $false)]
    [string]$WSUSServer,

    [Parameter(Mandatory = $false)]
    [switch]$SkipUpdates,

    [Parameter(Mandatory = $false)]
    [switch]$NoReboot,

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [string]$LogDirectory = 'C:\Logs'
)

#region Globals & Utilities

$script:LogFile      = $null
$script:Transcript   = $null
$script:PendingReboot = $false
$script:DryRun = $false

function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Message,
        [Parameter()][ValidateSet('INFO','WARN','ERROR','DEBUG')]
        [string]$Level = 'INFO'
    )
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line = "[{0}] [{1}] {2}" -f $timestamp, $Level, $Message
    if ($script:LogFile) {
        try { $line | Out-File -FilePath $script:LogFile -Append -Encoding UTF8 } catch {}
    }
    Write-Host $line
}

function Initialize-Logging {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$LogPath
    )
    try {
        if (-not (Test-Path -Path $LogPath)) {
            Execute-OrDryRun -Description "Create log directory $LogPath" -Action { New-Item -Path $LogPath -ItemType Directory -Force | Out-Null }
        }
        $stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
        $script:LogFile    = Join-Path $LogPath "ServerSetup_$stamp.log"
        $script:Transcript = Join-Path $LogPath "ServerSetup_$stamp.transcript.txt"
        Execute-OrDryRun -Description "Start transcript at $script:Transcript" -Action { Start-Transcript -Path $script:Transcript -Force | Out-Null }
        Write-Log "Logging initialized. Log: $script:LogFile; Transcript: $script:Transcript"
    } catch {
        Write-Log "Failed to initialize logging: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

function Stop-Logging {
    [CmdletBinding()]
    param()
    try { Stop-Transcript | Out-Null } catch {}
}

# Rollback framework: register reversible changes and rollback in reverse order
$script:AppliedChanges = @()

function Register-AppliedChange {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Type,
        [Parameter(Mandatory=$true)][string]$Description,
        [Parameter(Mandatory=$true)][scriptblock]$RevertScript
    )
    $obj = [pscustomobject]@{
        Type = $Type
        Description = $Description
        Revert = $RevertScript
    }
    $script:AppliedChanges += $obj
    Write-Log "Registered applied change: $Type - $Description" 'DEBUG'
}

function Rollback-AppliedChanges {
    [CmdletBinding()]
    param()
    if (-not $script:AppliedChanges -or $script:AppliedChanges.Count -eq 0) { Write-Log "No applied changes to rollback."; return }
    Write-Log "Starting rollback of $($script:AppliedChanges.Count) applied changes..." 'WARN'
    for ($i = $script:AppliedChanges.Count - 1; $i -ge 0; $i--) {
        $c = $script:AppliedChanges[$i]
        try {
            Write-Log "Rolling back: $($c.Type) - $($c.Description)" 'WARN'
            & $c.Revert
            Write-Log "Rolled back: $($c.Description)" 'INFO'
        } catch {
            Write-Log "Rollback failed for $($c.Description): $($_.Exception.Message)" 'ERROR'
        }
    }
    # clear applied changes after attempt
    $script:AppliedChanges = @()
    Write-Log "Rollback complete." 'WARN'
}

# Helper to execute an action or report it in dry-run mode
function Execute-OrDryRun {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Description,
        [Parameter(Mandatory=$true)][scriptblock]$Action
    )
    if ($script:DryRun) {
        Write-Log "DRY-RUN: $Description" 'INFO'
    } else {
        & $Action
    }
}

function Test-IsAdmin {
    [CmdletBinding()]
    param()
    try {
        $wi = [Security.Principal.WindowsIdentity]::GetCurrent()
        $wp = New-Object Security.Principal.WindowsPrincipal($wi)
        return $wp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch { return $false }
}

function Test-IPv4Address {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Address)
    if ($Address -notmatch '^(\d{1,3}\.){3}\d{1,3}$') { return $false }
    $octets = $Address.Split('.') | ForEach-Object {[int]$_}
    foreach ($o in $octets) { if ($o -lt 0 -or $o -gt 255) { return $false } }
    # disallow 0.0.0.0 and 255.255.255.255
    if ($Address -eq '0.0.0.0' -or $Address -eq '255.255.255.255') { return $false }
    return $true
}

function Convert-SubnetMaskToPrefixLength {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Mask)
    $octets = $Mask.Split('.')
    if ($octets.Count -ne 4) { throw "Invalid subnet mask: $Mask" }
    $bits = 0
    foreach ($o in $octets) {
        $n = [int]$o
        if ($n -lt 0 -or $n -gt 255) { throw "Invalid subnet mask octet: $o" }
        $bits += ([Convert]::ToString($n,2).ToCharArray() | Where-Object { $_ -eq '1' }).Count
    }
    return $bits
}

function Test-PendingReboot {
    [CmdletBinding()]
    param()
    $keys = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'
    )
    foreach ($k in $keys) { if (Test-Path $k) { return $true } }
    try {
        $pfro = Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' -Name 'PendingFileRenameOperations' -ErrorAction SilentlyContinue
        if ($pfro -and $pfro.PendingFileRenameOperations) { return $true }
    } catch {}
    return $false
}

function Get-PrimaryInterface {
    [CmdletBinding()]
    param([string]$Alias)
    if ($Alias) {
        $nic = Get-NetAdapter -Name $Alias -ErrorAction SilentlyContinue
        if (-not $nic) { throw "Interface '$Alias' not found." }
        if ($nic.Status -ne 'Up') { Write-Log "Interface '$Alias' is not Up; continuing." 'WARN' }
        return $nic.Name
    }
    $nic = Get-NetAdapter |
      Where-Object { $_.Status -eq 'Up' -and $_.Name -notmatch 'Loopback|isatap|Teredo|Bluetooth|VMware|Virtual|Hyper-V' } |
      Sort-Object -Property ifIndex | Select-Object -First 1
    if (-not $nic) { throw "No suitable network interface found in 'Up' state." }
    return $nic.Name
}

function Import-AnswerFile {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) { throw "ConfigPath '$Path' not found." }
    $ext = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    if ($ext -eq '.json') {
        $obj = Get-Content -Path $Path -Raw | ConvertFrom-Json
        if (-not $obj) { throw "JSON answer file is empty or invalid." }
        return $obj
    } elseif ($ext -eq '.csv') {
        $content = Get-Content -Path $Path -Raw
        Write-Host "CSV content read by Get-Content: $content"
        $rows = $content | ConvertFrom-Csv
        # Normalize to an array so single-row CSVs are handled consistently
        if ($rows) { $rows = @($rows) } else { $rows = @() }
        Write-Host "ConvertFrom-Csv returned $($rows.Count) rows."
        if ($rows.Count -lt 1) { throw "CSV answer file has no rows." }
        return $rows[0]
    } else {
        throw "Unsupported answer file type: $ext (use .json or .csv)."
    }
}

#endregion

#region Base Configuration

function Set-SystemConfig {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$NewHostname,
        [Parameter(Mandatory=$true)][string]$TimeZoneId
    )
    try {
        $current = (Get-CimInstance Win32_ComputerSystem).Name
        Write-Log "Current hostname: $current; Desired: $NewHostname"
        if ($current -ne $NewHostname) {
            if ($PSCmdlet.ShouldProcess("ComputerName", "Rename to '$NewHostname'")) {
                Execute-OrDryRun -Description "Rename computer to $NewHostname" -Action { Rename-Computer -NewName $NewHostname -Force -ErrorAction Stop; Write-Log "Computer rename scheduled to '$NewHostname'. Reboot required."; $script:PendingReboot = $true }
            }
        } else { Write-Log "Hostname already '$NewHostname'; no change." }

        if ($PSCmdlet.ShouldProcess("Time Zone", "Set to '$TimeZoneId'")) {
            try {
                Execute-OrDryRun -Description "Set time zone to $TimeZoneId" -Action { Set-TimeZone -Id $TimeZoneId -ErrorAction Stop; Write-Log "Time zone set to '$TimeZoneId'." }
            } catch {
                Write-Log "Failed to set time zone: $($_.Exception.Message)" 'ERROR'
                throw
            }
        }
    } catch {
        Write-Log "Set-SystemConfig failed: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

function Set-NetworkConfig {
    [CmdletBinding()]
    param(
        [Parameter()][string]$Alias,
        [Parameter()][string]$IPv4,
        [Parameter()][int]$Prefix,
        [Parameter()][string]$Gateway,
        [Parameter()][string[]]$Dns,
        [Parameter()][string]$Mask
    )
    try {
        $targetAlias = Get-PrimaryInterface -Alias $Alias
        Write-Log "Target interface: $targetAlias"
        # capture existing IPv4 addresses for rollback purposes
        $prevAddrs = @(Get-NetIPAddress -InterfaceAlias $targetAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -ne '127.0.0.1' } | Select-Object @{Name='IPAddress';Expression={$_.IPAddress}},@{Name='PrefixLength';Expression={$_.PrefixLength}})

        if ($IPv4) {
            if (-not (Test-IPv4Address -Address $IPv4)) { throw "Invalid IPv4 address: $IPv4" }
            if (-not $Prefix -and $Mask) {
                $Prefix = Convert-SubnetMaskToPrefixLength -Mask $Mask
                Write-Log "Converted SubnetMask '$Mask' to PrefixLength '$Prefix'."
            }
            if (-not $Prefix) { throw "PrefixLength or SubnetMask is required when setting IpAddress." }
            if ($Gateway -and -not (Test-IPv4Address -Address $Gateway)) { throw "Invalid Gateway IPv4 address: $Gateway" }

            if ($PSCmdlet.ShouldProcess("Interface '$targetAlias'", "Configure IPv4 $IPv4/$Prefix Gateway=$Gateway")) {
                try {
                    Execute-OrDryRun -Description "Disable DHCP on interface $targetAlias" -Action { Set-NetIPInterface -InterfaceAlias $targetAlias -Dhcp Disabled -ErrorAction SilentlyContinue }
                    Execute-OrDryRun -Description "Remove existing IPv4 addresses on $targetAlias" -Action { Get-NetIPAddress -InterfaceAlias $targetAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                        Where-Object { $_.IPAddress -ne '127.0.0.1' } | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue }
                    Execute-OrDryRun -Description "Add IPv4 $IPv4/$Prefix to $targetAlias with gateway $Gateway" -Action { New-NetIPAddress -InterfaceAlias $targetAlias -IPAddress $IPv4 -PrefixLength $Prefix -DefaultGateway $Gateway -AddressFamily IPv4 -ErrorAction Stop | Out-Null }
                    Write-Log "IPv4 configuration applied: $IPv4/$Prefix with gateway $Gateway."
                    # register rollback: remove the newly added IP and restore previous IPs (only if not dry-run)
                    if (-not $script:DryRun) {
                        $rbTarget = $targetAlias; $rbNewIp = $IPv4; $rbPrev = $prevAddrs
                        $revertScript = {
                            foreach ($a in $rbPrev) {
                                try { New-NetIPAddress -InterfaceAlias $rbTarget -IPAddress $a.IPAddress -PrefixLength $a.PrefixLength -ErrorAction SilentlyContinue } catch {}
                            }
                            try { Remove-NetIPAddress -InterfaceAlias $rbTarget -IPAddress $rbNewIp -Confirm:$false -ErrorAction SilentlyContinue } catch {}
                        }
                        Register-AppliedChange -Type 'Network' -Description "IPv4 $IPv4 on $targetAlias" -RevertScript $revertScript
                    }
                } catch {
                    Write-Log "Failed to set IPv4 config: $($_.Exception.Message)" 'ERROR'
                    throw
                }
            }
        } else { Write-Log "No IpAddress provided; skipping IP configuration." }

        if ($Dns) {
            foreach ($d in $Dns) { if (-not (Test-IPv4Address -Address $d)) { throw "Invalid DNS IPv4 address: $d" } }
            if ($PSCmdlet.ShouldProcess("Interface '$targetAlias'", "Set DNS servers: $($Dns -join ',')")) {
                try {
                    Set-DnsClientServerAddress -InterfaceAlias $targetAlias -ServerAddresses $Dns -ErrorAction Stop
                    Write-Log "DNS servers set to: $($Dns -join ',')."
                } catch {
                    Write-Log "Failed to set DNS servers: $($_.Exception.Message)" 'ERROR'
                    throw
                }
            }
        } else { Write-Log "No DNS servers provided; skipping DNS configuration." }
    } catch {
        Write-Log "Set-NetworkConfig failed: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

#endregion

#region Role Installation & Post-Config

function Invoke-InstallWindowsFeature {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][ValidateSet('Web-Server','DNS')][string]$Name)
    $isPS7 = ($PSVersionTable.PSVersion.Major -ge 7)
    try {
        if ($script:DryRun) {
            Write-Log "DRY-RUN: Would install Windows Feature '$Name' (no changes applied)." 'INFO'
            return
        }
        if (-not $isPS7) {
            Import-Module ServerManager -ErrorAction Stop
            Write-Log "Installing Windows Feature '$Name' via Install-WindowsFeature (PS 5.1)..."
            $result = Install-WindowsFeature -Name $Name -IncludeManagementTools -ErrorAction Stop
            if ($result.Success) { Write-Log "Feature '$Name' installed successfully." } else { Write-Log "Feature '$Name' install did not report success." 'WARN' }
            if ($result.RestartNeeded -and $result.RestartNeeded -ne 'No') { Write-Log "Feature '$Name' requested restart."; $script:PendingReboot = $true }
            # register uninstall for rollback (best-effort)
            try {
                $revertCmd = "try { Uninstall-WindowsFeature -Name '$Name' -ErrorAction SilentlyContinue } catch {}"
                $revertScript = [ScriptBlock]::Create($revertCmd)
                if (-not $script:DryRun) { Register-AppliedChange -Type 'Feature' -Description "Installed feature $Name" -RevertScript $revertScript }
            } catch { Write-Log ("Failed to register feature rollback for {0}: {1}" -f $Name, $_.Exception.Message) 'WARN' }
        } else {
            $pwsh5Path = Get-Command -Name powershell.exe -ErrorAction SilentlyContinue
            if (-not $pwsh5Path) {
                throw "powershell.exe not found. Cannot install roles from PowerShell 7 on this system without it."
            }

            $cmd = "Import-Module ServerManager -ErrorAction Stop; Install-WindowsFeature -Name '$Name' -IncludeManagementTools -ErrorAction Stop"
            $encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($cmd))

            Write-Log "Installing Windows Feature '$Name' via Windows PowerShell (ServerManager)..."
            $processInfo = New-Object System.Diagnostics.ProcessStartInfo
            $processInfo.FileName = $pwsh5Path.Source
            $processInfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
            $processInfo.RedirectStandardError = $true
            $processInfo.RedirectStandardOutput = $true
            $processInfo.UseShellExecute = $false
            $processInfo.CreateNoWindow = $true

            $p = New-Object System.Diagnostics.Process
            $p.StartInfo = $processInfo
            $p.Start() | Out-Null
            $p.WaitForExit()

            $stdout = $p.StandardOutput.ReadToEnd()
            $stderr = $p.StandardError.ReadToEnd()

            if ($p.ExitCode -eq 0) {
                Write-Log "Feature '$Name' installed successfully (PS 7+ via Windows PowerShell)."
                if ($stdout) { Write-Log "PS 5.1 stdout: $stdout" 'DEBUG' }
            } else {
                throw "External Install-WindowsFeature failed with exit code $($p.ExitCode). Stderr: $stderr"
            }
            $script:PendingReboot = $script:PendingReboot -or (Test-PendingReboot)
            # register uninstall via external powershell.exe for rollback
            try {
                $pwPath = $pwsh5Path.Source -replace "'","''"
                $uninstallCmd = "Import-Module ServerManager -ErrorAction Stop; Uninstall-WindowsFeature -Name '$Name' -ErrorAction SilentlyContinue"
                $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($uninstallCmd))
                $revertCmd = "`$p = New-Object System.Diagnostics.ProcessStartInfo; `$p.FileName = '$pwPath'; `$p.Arguments = '-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded'; `$p.RedirectStandardOutput = `$true; `$p.RedirectStandardError = `$true; `$p.UseShellExecute = `$false; `$p.CreateNoWindow = `$true; `$pr = New-Object System.Diagnostics.Process; `$pr.StartInfo = `$p; `$pr.Start() | Out-Null; `$pr.WaitForExit()"
                $revertScript = [ScriptBlock]::Create($revertCmd)
                Register-AppliedChange -Type 'Feature' -Description "Installed feature $Name (external)" -RevertScript $revertScript
            } catch { Write-Log ("Failed to register external feature rollback for {0}: {1}" -f $Name, $_.Exception.Message) 'WARN' }
        }
    } catch {
        Write-Log "Invoke-InstallWindowsFeature failed for '$Name': $($_.Exception.Message)" 'ERROR'
        throw
    }
}

function Configure-IISPostInstall {
    [CmdletBinding()]
    param([switch]$CreateIndex,[switch]$EnableFirewall)
    try {
        Write-Log "Configuring IIS post-install..."
        if ($script:DryRun) { Write-Log "DRY-RUN: Would configure IIS post-install (CreateIndex=$CreateIndex, EnableFirewall=$EnableFirewall)" 'INFO'; return }
        # Ensure web root exists
        $webroot = 'C:\inetpub\wwwroot'
        $webrootExisted = Test-Path $webroot
        if (-not $webrootExisted) { New-Item -ItemType Directory -Path $webroot -Force | Out-Null }

        if ($CreateIndex) {
            $hostname = (Get-CimInstance Win32_ComputerSystem).Name
            $content = @"
<!doctype html>
<html>
<head><meta charset=\"utf-8\"><title>Fabrikam IIS</title>
<style>body{font-family:Segoe UI,Arial;margin:40px;background:#f7f7f7;color:#333} .card{padding:24px;background:white;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1)}</style>
</head>
<body><div class=\"card\"><h1>Fabrikam Web Server</h1><p>Host: $hostname</p><p>IIS installed and configured automatically.</p></div></body>
</html>
"@
            $indexPath = Join-Path $webroot 'index.html'
            $content | Out-File -FilePath $indexPath -Encoding UTF8 -Force
            Write-Log "Default index.html created at $indexPath"
            # register rollback to remove created file and (optionally) created webroot
            $rbFile = $indexPath; $rbWebrootExisted = $webrootExisted
            $revertIIS = {
                try { Remove-Item -Path $rbFile -Force -ErrorAction SilentlyContinue } catch {}
                if (-not $rbWebrootExisted) {
                    try { Remove-Item -Path (Split-Path $rbFile -Parent) -Recurse -Force -ErrorAction SilentlyContinue } catch {}
                }
            }
            Register-AppliedChange -Type 'IIS' -Description "Default index.html at $indexPath" -RevertScript $revertIIS
        }

        if ($EnableFirewall) {
            try {
                Get-NetFirewallRule | Where-Object { $_.DisplayName -match 'World Wide Web Services' -or $_.DisplayName -match 'HTTP' -or $_.DisplayName -match 'HTTPS' } | Enable-NetFirewallRule -ErrorAction SilentlyContinue
                Write-Log "Enabled inbound firewall rules for HTTP/HTTPS (where available)."
            } catch { Write-Log "Failed to enable firewall rules: $($_.Exception.Message)" 'WARN' }
        }
    } catch {
        Write-Log "Configure-IISPostInstall failed: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

function Configure-DNSPostInstall {
    [CmdletBinding()]
    param([string]$ZoneName,[hashtable[]]$Records)
    try {
        Write-Log "Configuring DNS post-install..."
        if ($script:DryRun) { Write-Log "DRY-RUN: Would configure DNS zone and records for $ZoneName" 'INFO'; return }
        Import-Module DnsServer -ErrorAction Stop
        if ($ZoneName) {
            $zoneExisted = (Get-DnsServerZone -Name $ZoneName -ErrorAction SilentlyContinue)
            if (-not $zoneExisted) {
                if ($PSCmdlet.ShouldProcess("DNS", "Create primary zone '$ZoneName'")) {
                    Add-DnsServerPrimaryZone -Name $ZoneName -ZoneFile "$ZoneName.dns" -DynamicUpdate None -ErrorAction Stop | Out-Null
                    Write-Log "DNS primary zone created: $ZoneName"
                    # register rollback for created zone
                    $rbZone = $ZoneName
                    $revertZone = { try { Remove-DnsServerZone -Name $rbZone -Force -ErrorAction SilentlyContinue } catch {} }
                    Register-AppliedChange -Type 'DNS' -Description "Primary zone $ZoneName" -RevertScript $revertZone
                }
            } else { Write-Log "DNS zone '$ZoneName' already exists; skipping." }
        }
        if ($ZoneName -and $Records) {
            foreach ($rec in $Records) {
                $n = $rec.Name
                $ip = $rec.IPv4
                if (-not $n -or -not $ip) { Write-Log "Skipping record with missing Name/IPv4." 'WARN'; continue }
                if (-not (Test-IPv4Address -Address $ip)) { Write-Log "Skipping invalid IPv4 for record '$n': $ip" 'WARN'; continue }
                if ($PSCmdlet.ShouldProcess("DNS", "Add A record $n -> $ip in $ZoneName")) {
                    try {
                        Add-DnsServerResourceRecordA -ZoneName $ZoneName -Name $n -IPv4Address $ip -TimeToLive ([TimeSpan]::FromMinutes(15)) -ErrorAction Stop | Out-Null
                        Write-Log "Added A record: $n.$ZoneName -> $ip"
                        # register rollback for this record
                        $rbName = $n; $rbZoneName = $ZoneName
                        $revertRec = { try { Remove-DnsServerResourceRecord -ZoneName $rbZoneName -Name $rbName -RRType 'A' -Force -ErrorAction SilentlyContinue } catch {} }
                        Register-AppliedChange -Type 'DNS' -Description "A record $n.$ZoneName -> $ip" -RevertScript $revertRec
                    } catch {
                        $errorMessage = $_.Exception.Message
                        Write-Log "Failed to add record ${n}: ${errorMessage}" 'ERROR'
                    }
                }
            }
        }
    } catch {
        Write-Log "Configure-DNSPostInstall failed: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

function Install-ServerRoles {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string[]]$RoleNames)
    foreach ($r in $RoleNames) {
        if ($PSCmdlet.ShouldProcess("WindowsFeature:$r", "Install")) { Invoke-InstallWindowsFeature -Name $r }
        switch ($r) {
            'Web-Server' { Configure-IISPostInstall -CreateIndex:$CreateDefaultIISPage -EnableFirewall:$EnableWebFirewallRules }
            'DNS'        { Configure-DNSPostInstall -ZoneName $DnsZoneName -Records $DnsRecords }
        }
    }
}

#endregion

#region Windows Update & WSUS

function Configure-WSUSPolicy {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ServerUrl)
    try {
        Write-Log "Configuring WSUS policy to '$ServerUrl'..."
        if ($script:DryRun) { Write-Log "DRY-RUN: Would configure WSUS policy to '$ServerUrl'" 'INFO'; return }
        $wuKey = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate'
        $auKey = "$wuKey\AU"
        # capture previous values for rollback
        $prev = @{}
        $prev.Exists = Test-Path $wuKey
        $prev.WUServer = (Get-ItemProperty -Path $wuKey -Name 'WUServer' -ErrorAction SilentlyContinue).WUServer
        $prev.WUStatusServer = (Get-ItemProperty -Path $wuKey -Name 'WUStatusServer' -ErrorAction SilentlyContinue).WUStatusServer
        $prev.UseWUServer = (Get-ItemProperty -Path $auKey -Name 'UseWUServer' -ErrorAction SilentlyContinue).UseWUServer

        New-Item -Path $wuKey -Force | Out-Null
        New-Item -Path $auKey -Force | Out-Null
        Set-ItemProperty -Path $wuKey -Name 'WUServer' -Value $ServerUrl -Force
        Set-ItemProperty -Path $wuKey -Name 'WUStatusServer' -Value $ServerUrl -Force
        Set-ItemProperty -Path $auKey -Name 'UseWUServer' -Value 1 -Force
        Write-Log "WSUS registry policy set. Restarting Windows Update service..."
        Restart-Service -Name wuauserv -Force

        # register rollback to restore previous WSUS registry state
        try {
            if ($prev.WUServer -ne $null) { $rbWUServer = $prev.WUServer -replace "'","''" } else { $rbWUServer = $null }
            if ($prev.WUStatusServer -ne $null) { $rbWUStatus = $prev.WUStatusServer -replace "'","''" } else { $rbWUStatus = $null }
            if ($null -ne $prev.UseWUServer) { $rbUseWUServer = $prev.UseWUServer } else { $rbUseWUServer = $null }
            $rbExists = $prev.Exists
            $revertScript = [ScriptBlock]::Create(
                "`$wuKey = '$wuKey'; `$auKey = '$auKey';`n" +
                (if (-not $rbExists) {
                    "try { Remove-Item -Path `$wuKey -Recurse -Force -ErrorAction SilentlyContinue } catch {}"
                } else {
                    "try {"
                    + (if ($rbWUServer) { " Set-ItemProperty -Path `$wuKey -Name 'WUServer' -Value '$rbWUServer' -Force -ErrorAction SilentlyContinue;" } else { " Remove-ItemProperty -Path `$wuKey -Name 'WUServer' -ErrorAction SilentlyContinue;" })
                    + (if ($rbWUStatus) { " Set-ItemProperty -Path `$wuKey -Name 'WUStatusServer' -Value '$rbWUStatus' -Force -ErrorAction SilentlyContinue;" } else { " Remove-ItemProperty -Path `$wuKey -Name 'WUStatusServer' -ErrorAction SilentlyContinue;" })
                    + (if ($rbUseWUServer -ne $null) { " Set-ItemProperty -Path `$auKey -Name 'UseWUServer' -Value $rbUseWUServer -Force -ErrorAction SilentlyContinue;" } else { " Remove-ItemProperty -Path `$auKey -Name 'UseWUServer' -ErrorAction SilentlyContinue;" })
                    + " } catch {} `n try { Restart-Service -Name wuauserv -Force } catch {}"
                })
            )
            Register-AppliedChange -Type 'WSUS' -Description "WSUS policy set to $ServerUrl" -RevertScript $revertScript
        } catch { Write-Log ("Failed to register WSUS rollback: {0}" -f $_.Exception.Message) 'WARN' }
    } catch {
        Write-Log "Failed to configure WSUS policy: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

function Invoke-WindowsUpdate {
    [CmdletBinding()]
    param([switch]$UseManagedSource)
    try {
        if ($UseManagedSource -and $WSUSServer) { Configure-WSUSPolicy -ServerUrl $WSUSServer }
        Write-Log "Checking Windows Updates via Microsoft.Update.Session (COM)..."
        $session = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        if ($UseManagedSource) { $searcher.ServerSelection = 1 } # ssManagedServer
        $criteria = "IsInstalled=0 and Type='Software' and IsHidden=0"
        $result = $searcher.Search($criteria)
        $count = $result.Updates.Count
        Write-Log "Found $count applicable updates."
        if ($count -gt 0 -and $PSCmdlet.ShouldProcess("Windows Update", "Download & Install $count updates")) {
            $updatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
            for ($i = 0; $i -lt $result.Updates.Count; $i++) { $updatesToInstall.Add($result.Updates.Item($i)) | Out-Null }
            Write-Log "Downloading updates..."
            if ($script:DryRun) {
                Write-Log "DRY-RUN: Would download and install $count updates (skipped)." 'INFO'
            } else {
                $downloader = $session.CreateUpdateDownloader(); $downloader.Updates = $updatesToInstall; $downloader.Download() | Out-Null
                Write-Log "Installing updates..."
                $installer = $session.CreateUpdateInstaller(); $installer.Updates = $updatesToInstall; $installResult = $installer.Install()
                Write-Log "Install result: $($installResult.ResultCode); RebootRequired: $($installResult.RebootRequired)"
                if ($installResult.RebootRequired) { Write-Log "Windows Update reports reboot required."; $script:PendingReboot = $true }
            }
        } else { Write-Log "No updates to install or operation skipped." }
    } catch {
        Write-Log "Invoke-WindowsUpdate failed: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

#endregion

#region Reboot Handling

function Invoke-RebootIfNeeded {
    [CmdletBinding()]
    param([switch]$Suppress)
    try {
        $pending = $script:PendingReboot -or (Test-PendingReboot)
        if ($pending) {
            Write-Log "System indicates a pending reboot."
            if (-not $Suppress) {
                if ($PSCmdlet.ShouldProcess("Computer", "Restart immediately")) {
                    Write-Log "Restarting computer in 10 seconds..."; Start-Sleep -Seconds 10; Restart-Computer -Force
                }
            } else { Write-Log "Reboot suppressed by -NoReboot." }
        } else { Write-Log "No reboot required." }
    } catch { Write-Log "Invoke-RebootIfNeeded failed: $($_.Exception.Message)" 'ERROR'; throw }
}

#endregion

#region Main Orchestration

if ($global:IsTestMode -ne $true) {
    try {
    # honor DryRun parameter
    $script:DryRun = $DryRun.IsPresent -or $script:DryRun
    if (-not (Test-IsAdmin)) { throw "This script must be run as an Administrator." }

    # Parameter validation
    if ($IpAddress) {
        if (-not ($PrefixLength -or $SubnetMask)) {
            throw "When -IpAddress is specified, you must also provide either -PrefixLength or -SubnetMask."
        }
        if (-not $DefaultGateway) {
            throw "When -IpAddress is specified, you must also provide -DefaultGateway."
        }
        if (-not $DnsServers) {
            throw "When -IpAddress is specified, you must also provide -DnsServers."
        }
    }
    # Answer file merge (pre-fill)
    if ($ConfigPath) {
        $cfg = Import-AnswerFile -Path $ConfigPath
        foreach ($k in $cfg.PSObject.Properties.Name) {
            if ($PSBoundParameters.ContainsKey($k)) { continue } # don't override provided params
            Set-Variable -Name $k -Value $cfg.$k -Scope Script -ErrorAction SilentlyContinue
        }
    }

    Initialize-Logging -LogPath $LogDirectory

    Write-Log "=== Fabrikam Server Setup (Extended) started ==="
    Write-Log "Parameters: Hostname=$Hostname; IpAddress=$IpAddress; PrefixLength=$PrefixLength; SubnetMask=$SubnetMask; Gateway=$DefaultGateway; Dns=$($DnsServers -join ','); Roles=$($Roles -join ','); TimeZone=$TimeZone; InterfaceAlias=$InterfaceAlias; IISPage=$($CreateDefaultIISPage.IsPresent); WebFirewall=$($EnableWebFirewallRules.IsPresent); DnsZone=$DnsZoneName; WSUS=$($UseWSUS.IsPresent); WSUSServer=$WSUSServer; SkipUpdates=$($SkipUpdates.IsPresent); NoReboot=$($NoReboot.IsPresent); ConfigPath=$ConfigPath" 'DEBUG'

    # 1. Base configuration
    Set-SystemConfig -NewHostname $Hostname -TimeZoneId $TimeZone

    # 2. Networking
    Set-NetworkConfig -Alias $InterfaceAlias -IPv4 $IpAddress -Prefix $PrefixLength -Gateway $DefaultGateway -Dns $DnsServers -Mask $SubnetMask

    # 3. Roles + post-config
    Install-ServerRoles -RoleNames $Roles

    # 4. Updates (optional)
    if (-not $SkipUpdates) { Invoke-WindowsUpdate -UseManagedSource:$UseWSUS } else { Write-Log "Windows Updates skipped by -SkipUpdates." }

    # 5. Reboot when needed
    Invoke-RebootIfNeeded -Suppress:$NoReboot

    Write-Log "=== Fabrikam Server Setup (Extended) completed ==="
} catch {
    Write-Log "Fatal error: $($_.Exception.Message)" 'ERROR'
    try {
        # attempt rollback of applied changes where possible
        Rollback-AppliedChanges
    } catch {
        Write-Log "Rollback attempt failed: $($_.Exception.Message)" 'ERROR'
    }
    Write-Log "Script terminated with errors. Check transcript and log for details." 'ERROR'
    } finally { Stop-Logging }
}

#endregion
