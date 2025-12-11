Developer Documentation — Setup-FabrikamServer-Extended

Purpose

Provide developers with design rationale, function reference, testing guidance, and extension points for `Setup-FabrikamServer-Extended.ps1`.

Architecture & Design

- Modular functions grouped into regions: Globals & Utilities, Base Configuration, Role Installation & Post-Config, Windows Update & WSUS, Reboot Handling, Main Orchestration.
- Functions are small, single-responsibility, and use `CmdletBinding()` to support advanced parameters and `ShouldProcess`.
- Logging centralised via `Write-Log` and transcript support to provide consistent debug and audit trails.

Key functions (summary)

- `Write-Log(Message, Level)` — centralized logging.
- `Initialize-Logging(LogPath)` — prepares `C:\Logs`, log and transcript file paths.
- `Test-IsAdmin()` — returns boolean; ensures script runs elevated.
- `Test-IPv4Address(Address)` — regex + numeric range validation.
- `Convert-SubnetMaskToPrefixLength(Mask)` — converts dotted mask to CIDR prefix.
- `Get-PrimaryInterface(Alias)` — resolves network adapter to configure.
- `Import-AnswerFile(Path)` — reads JSON or CSV and returns an object with properties pre-filled for script parameters. Note: CSV import normalizes ConvertFrom-Csv result to an array to support single-row CSVs.
- `Set-SystemConfig(NewHostname, TimeZoneId)` — sets hostname & time zone.
- `Set-NetworkConfig(Alias, IPv4, Prefix, Gateway, Dns, Mask)` — configures IPv4 and DNS.
- `Invoke-InstallWindowsFeature(Name)` — handles installation across PS versions (calls Windows PowerShell for 5.1 features if needed).
- `Configure-IISPostInstall` / `Configure-DNSPostInstall` — role-specific tasks.

Coding standards & best practices used

- Functions include `CmdletBinding()` for consistent parameter behavior.
- Use of `try/catch` with error logging to avoid silent failures.
- Avoid side-effects in helper functions; main orchestration handles order and `ShouldProcess`.
- Parameter validation with attributes (e.g., `ValidateRange`, `ValidatePattern`) where appropriate.

Testing and CI suggestions

- Keep Pester tests for helper functions and parsing logic; consider adding integration-style tests that run in a disposable VM.
- Add a `build` pipeline step that runs PSScriptAnalyzer and Pester tests.
- Recommended pipeline steps:
  - `PowerShell` linting with `Invoke-ScriptAnalyzer`.
  - `Invoke-Pester` for tests.

Extension points

- DSC: create a configuration resource wrapper around `Set-SystemConfig` and `Set-NetworkConfig`.
- Windows Admin Center: build an extension that reads the same answer file format and invokes the script remotely.
- Support for additional roles: add role-specific `Configure-*PostInstall` functions and include in `Install-ServerRoles` orchestration.

Notes on CSV import edge cases

- ConvertFrom-Csv may return a single object instead of a collection. The script normalizes result to an array (`@($rows)`) to ensure `.Count` is available and consistent.

Developer workflow

- Open the script in VS Code with PowerShell extension for intellisense and integrated Pester runner.
- Run `Invoke-Pester` locally when modifying helper functions.
- When editing role installation code, test in a disposable VM to avoid system changes on developer machines.
