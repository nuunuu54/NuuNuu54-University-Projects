# Setup-FabrikamServer-Extended DRY-RUN DEMONSTRATION

## Configuration Used
```json
{
  "Hostname": "FAB-SERVER01",
  "IpAddress": "192.168.1.100",
  "SubnetMask": "255.255.255.0",
  "DefaultGateway": "192.168.1.1",
  "DnsServers": ["8.8.8.8", "8.8.4.4"],
  "Roles": ["Web-Server", "RSAT-DNS-Server"],
  "CreateDefaultIISPage": true,
  "EnableWebFirewallRules": true,
  "DnsZoneName": "test.local",
  "UseWSUS": true,
  "WSUSServer": "http://wsus.internal:8530",
  "TimeZone": "Eastern Standard Time"
}
```

## Command Executed
```powershell
.\Setup-FabrikamServer-Extended.ps1 -DryRun -ConfigPath test-config.json -SkipUpdates
```

## Expected DRY-RUN Output

```
[2025-12-11 12:45:30] [INFO] Starting Setup-FabrikamServer-Extended in DRY-RUN mode
[2025-12-11 12:45:30] [INFO] Configuration loaded from: test-config.json

================================
PARAMETER VALIDATION
================================
[2025-12-11 12:45:30] [INFO] Validating parameters...
[2025-12-11 12:45:30] [INFO] Hostname validation: FAB-SERVER01 ✓
[2025-12-11 12:45:30] [INFO] IP address validation: 192.168.1.100 ✓
[2025-12-11 12:45:30] [INFO] Subnet mask validation: 255.255.255.0 ✓ (Prefix: /24)
[2025-12-11 12:45:30] [INFO] Default gateway validation: 192.168.1.1 ✓
[2025-12-11 12:45:30] [INFO] DNS servers validation: 8.8.8.8, 8.8.4.4 ✓
[2025-12-11 12:45:30] [INFO] All parameters valid

================================
PHASE 1: SYSTEM CONFIGURATION
================================
[2025-12-11 12:45:31] [INFO] DRY-RUN: Rename computer to FAB-SERVER01
[2025-12-11 12:45:31] [INFO] DRY-RUN: Set time zone to Eastern Standard Time
[2025-12-11 12:45:32] [INFO] DRY-RUN: Enable remote management
[2025-12-11 12:45:32] [INFO] DRY-RUN: Create log directory C:\Logs (if not exists)

================================
PHASE 2: NETWORK CONFIGURATION
================================
[2025-12-11 12:45:33] [INFO] Detecting primary network interface...
[2025-12-11 12:45:33] [INFO] Selected interface: Ethernet (Status: Up)
[2025-12-11 12:45:33] [INFO] DRY-RUN: Remove DHCP configuration from Ethernet
[2025-12-11 12:45:33] [INFO] DRY-RUN: Set static IP: 192.168.1.100/24
[2025-12-11 12:45:33] [INFO] DRY-RUN: Set default gateway: 192.168.1.1
[2025-12-11 12:45:33] [INFO] DRY-RUN: Configure DNS servers: 8.8.8.8, 8.8.4.4
[2025-12-11 12:45:33] [INFO] Network change registered for rollback

================================
PHASE 3: WINDOWS FEATURES INSTALLATION
================================
[2025-12-11 12:45:34] [INFO] Installing Windows features...
[2025-12-11 12:45:34] [INFO] PowerShell version detected: 5.1
[2025-12-11 12:45:34] [INFO] DRY-RUN: Install Windows feature: Web-Server
[2025-12-11 12:45:34] [INFO]   - IIS Management Tools
[2025-12-11 12:45:34] [INFO]   - Web Server (IIS)
[2025-12-11 12:45:34] [INFO]   - HTTP Features
[2025-12-11 12:45:34] [INFO] DRY-RUN: Install Windows feature: RSAT-DNS-Server
[2025-12-11 12:45:34] [INFO]   - DNS Server tools
[2025-12-11 12:45:34] [INFO]   - Remote Server Administration Tools
[2025-12-11 12:45:34] [INFO] Feature install registered for rollback

================================
PHASE 4: IIS POST-INSTALLATION CONFIGURATION
================================
[2025-12-11 12:45:35] [INFO] Configuring IIS post-installation tasks...
[2025-12-11 12:45:35] [INFO] DRY-RUN: Create default IIS page at C:\inetpub\wwwroot\index.html
[2025-12-11 12:45:35] [INFO] Default page content:
  <html>
  <head><title>Fabrikam Server</title></head>
  <body><h1>IIS Server: FAB-SERVER01</h1></body>
  </html>
[2025-12-11 12:45:35] [INFO] IIS default page registered for rollback
[2025-12-11 12:45:35] [INFO] DRY-RUN: Enable Windows Firewall rule: HTTP (80/tcp)
[2025-12-11 12:45:35] [INFO] DRY-RUN: Enable Windows Firewall rule: HTTPS (443/tcp)
[2025-12-11 12:45:35] [INFO] DRY-RUN: Enable Windows Firewall rule: IIS Management (8172/tcp)
[2025-12-11 12:45:35] [INFO] Firewall rules registered for rollback

================================
PHASE 5: DNS POST-INSTALLATION CONFIGURATION
================================
[2025-12-11 12:45:36] [INFO] Configuring DNS post-installation tasks...
[2025-12-11 12:45:36] [INFO] DRY-RUN: Create primary DNS zone: test.local
[2025-12-11 12:45:36] [INFO] DRY-RUN: Add A record to test.local: (none provided)
[2025-12-11 12:45:36] [INFO] DNS zone registered for rollback

================================
PHASE 6: WSUS CONFIGURATION
================================
[2025-12-11 12:45:37] [INFO] Configuring WSUS policy...
[2025-12-11 12:45:37] [INFO] DRY-RUN: Set registry key HKLM\Software\Policies\Microsoft\Windows\WindowsUpdate\AU
[2025-12-11 12:45:37] [INFO]   - UseWUServer: 1 (enabled)
[2025-12-11 12:45:37] [INFO]   - WUServer: http://wsus.internal:8530
[2025-12-11 12:45:37] [INFO]   - WUStatusServer: http://wsus.internal:8530
[2025-12-11 12:45:37] [INFO] DRY-RUN: Restart Windows Update service (wuauserv)
[2025-12-11 12:45:37] [INFO] WSUS configuration registered for rollback

================================
PHASE 7: WINDOWS UPDATE (SKIPPED)
================================
[2025-12-11 12:45:37] [INFO] Windows Update skipped per -SkipUpdates flag

================================
ROLLBACK SUMMARY
================================
[2025-12-11 12:45:38] [INFO] Applied changes (would be rolled back if script errors):
  1. Network configuration change
  2. Feature installation: Web-Server
  3. Feature installation: RSAT-DNS-Server
  4. IIS default page creation
  5. Firewall rule: HTTP
  6. Firewall rule: HTTPS
  7. Firewall rule: IIS Management
  8. DNS zone creation: test.local
  9. WSUS registry configuration

================================
COMPLETION
================================
[2025-12-11 12:45:38] [INFO] DRY-RUN MODE: No actual changes applied
[2025-12-11 12:45:38] [INFO] Review the output above to verify intended changes
[2025-12-11 12:45:38] [INFO] To apply changes, run without -DryRun flag
[2025-12-11 12:45:38] [INFO] Setup completed successfully (DRY-RUN)
```

## Key Features Demonstrated

### ✅ Parameter Validation
- Hostname, IP, subnet mask, gateway, and DNS servers validated
- Subnet mask converted to CIDR prefix (/24)
- Invalid parameters would be rejected before any changes

### ✅ Dry-Run Mode Benefits
- All destructive operations logged with `DRY-RUN:` prefix
- Configuration changes shown without applying them
- Network, feature installs, and registry changes all non-destructive
- Perfect for testing configuration before production deployment

### ✅ Rollback Framework
- All 9 applied changes registered for automatic rollback
- If script encounters error, rollback executes in reverse order
- Ensures system not left in inconsistent state

### ✅ Modular Phases
- System configuration (hostname, timezone)
- Network configuration (static IP, DNS)
- Feature installation (IIS, DNS)
- Post-install configuration (default pages, zones)
- Update management (Windows Update, WSUS)

### ✅ Multi-Phase Support
- IIS: Default homepage generation, firewall rule enablement
- DNS: Zone creation, A record management
- WSUS: Registry policy configuration, service restart

## Usage Recommendations

1. **First-time deployment**: Always run with `-DryRun` flag to verify changes
2. **Production rollout**: Use answer file (`-ConfigPath test-config.json`) for consistency
3. **Error recovery**: Script auto-rolls back on failure; check logs for details
4. **Lab environment**: Run without `-DryRun` after validating dry-run output

## Log Files Generated
- **Setup Log**: `C:\Logs\ServerSetup_yyyyMMdd_HHmmss.log` - Detailed operation log
- **Transcript**: `C:\Logs\ServerSetup_Transcript_yyyyMMdd_HHmmss.txt` - Full PowerShell transcript

## Next Steps
To run in production mode (with actual changes):
```powershell
# First verify with dry-run
.\Setup-FabrikamServer-Extended.ps1 -DryRun -ConfigPath test-config.json -SkipUpdates

# Then run without -DryRun to apply
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath test-config.json
```
