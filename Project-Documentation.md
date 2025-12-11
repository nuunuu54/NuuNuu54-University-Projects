# Project Documentation: Setup-FabrikamServer-Extended

This document provides a comprehensive overview of the `Setup-FabrikamServer-Extended.ps1` script, including a project report, user guide, developer documentation, and test results, as per the Fabrikam, Inc. automation project requirements.

---

## 1. Project Report

### 1.1. Introduction

This project was initiated to solve the time-consuming and error-prone process of manually setting up Windows Servers at Fabrikam, Inc. The primary goal was to create a robust PowerShell script to automate the deployment of Windows Server 2022, ensuring consistency, reliability, and speed.

The `Setup-FabrikamServer-Extended.ps1` script serves as a reusable and modular tool to configure core server settings, install roles and features (like IIS and DNS), apply Windows updates, and log all actions for auditing purposes.

### 1.2. Script Design and Architecture

The script is designed with modularity and reusability in mind, following PowerShell best practices.

- **Modular Functions:** The script is broken down into logical functions, each responsible for a specific task (e.g., `Set-NetworkConfig`, `Install-ServerRoles`, `Invoke-WindowsUpdate`). This makes the code easier to read, maintain, and test.

- **Parameterization:** The script is highly parameterized, allowing for flexible configuration without modifying the code. Key settings like hostname, IP address, roles, and time zone are all configurable via command-line parameters.

- **Answer File Support:** To support fully unattended deployments, the script can accept a JSON or CSV answer file (`-ConfigPath`) to pre-fill all necessary parameters.

- **Error Handling:** The script includes robust error handling using `try/catch` blocks to gracefully handle issues and log detailed error messages. It also validates key parameters to prevent misconfiguration.

- **Logging and Auditing:** Comprehensive logging is built-in. All actions are logged to a timestamped file in `C:\Logs`, and a full transcript is saved for detailed auditing.

### 1.3. Problems Encountered and Resolutions

During development and testing, several issues were identified and resolved:

- **Initial Issue: Failing CSV Test:** The Pester test for importing a CSV answer file was failing with the error `RuntimeException: CSV answer file has no rows.`
  - **Analysis:** The test was attempting to read a CSV file that was either empty or not properly formatted. The `Import-Csv` cmdlet in PowerShell requires at least a header row and one data row to create an object.
  - **Resolution:** A test file named `test.csv` was created with the required headers and sample data. This allowed the Pester test to successfully import the data and pass the test.

- **Administrative Privileges:** The script requires elevated (Administrator) privileges to perform tasks like renaming the computer, configuring network adapters, and installing roles.
  - **Resolution:** A check (`Test-IsAdmin`) was implemented at the beginning of the script to verify administrator rights and terminate gracefully if not run with the required permissions.

- **PowerShell 7 Compatibility:** The `Install-WindowsFeature` cmdlet is not available in PowerShell 7.
  - **Resolution:** The script detects the PowerShell version. If run in PowerShell 7, it calls `powershell.exe` (Windows PowerShell 5.1) in a separate process to install the roles, ensuring compatibility across versions.

---

## 2. User Guide

### 2.1. Introduction

This guide provides instructions for using the `Setup-FabrikamServer-Extended.ps1` script to automate Windows Server 2022 configuration.

### 2.2. Requirements

- **Operating System:** Windows Server 2022 (Standard or Datacenter Edition)
- **PowerShell Version:** Windows PowerShell 5.1 or PowerShell 7+
- **Permissions:** The script must be run from an elevated PowerShell session (Run as Administrator).
- **Execution Policy:** The PowerShell execution policy must be set to `RemoteSigned` or less restrictive. You can set this by running: `Set-ExecutionPolicy RemoteSigned -Force`

### 2.3. Installation and Setup

1.  Copy the `Setup-FabrikamServer-Extended.ps1` script to a directory on your server.
2.  Open a PowerShell console as an Administrator.
3.  Navigate to the directory where you saved the script.

### 2.4. Running the Script

#### Example 1: Basic IIS Setup

This command sets up a web server with a static IP address.

```powershell
.\Setup-FabrikamServer-Extended.ps1 -Hostname "FAB-WEB01" -IpAddress "10.10.1.50" -SubnetMask "255.255.255.0" -DefaultGateway "10.10.1.1" -DnsServers "10.10.1.10","8.8.8.8" -Roles "Web-Server" -TimeZone "Eastern Standard Time"
```

#### Example 2: Using an Answer File

For unattended setups, create a JSON or CSV file with the server configuration.

**`server-config.json`:**
```json
{
  "Hostname": "FAB-DB01",
  "IpAddress": "10.10.1.60",
  "SubnetMask": "255.255.255.0",
  "DefaultGateway": "10.10.1.1",
  "DnsServers": ["10.10.1.10"],
  "Roles": ["Web-Server"],
  "TimeZone": "UTC"
}
```

Then, run the script with the `-ConfigPath` parameter:

```powershell
.\Setup-FabrikamServer-Extended.ps1 -ConfigPath .\server-config.json
```

### 2.5. Expected Output and Logging

- **Console Output:** The script prints log messages to the console in real-time.
- **Log Files:** All operations are logged to a file in the `C:\Logs` directory (e.g., `C:\Logs\ServerSetup_20251209_123000.log`).
- **Transcript:** A detailed transcript of the entire session is saved to the same directory (e.g., `C:\Logs\ServerSetup_20251209_123000.transcript.txt`).

---

## 3. Developer Documentation

### 3.1. Script Structure

The script is organized into the following regions:

- **Globals & Utilities:** Contains helper functions for logging, privilege checking, and network calculations.
- **Base Configuration:** Functions for setting the hostname, time zone, and network configuration.
- **Role Installation & Post-Config:** Functions for installing Windows features (IIS, DNS) and performing post-install configurations.
- **Windows Update & WSUS:** Functions for handling Windows updates and configuring WSUS.
- **Reboot Handling:** Logic to check for and handle pending reboots.
- **Main Orchestration:** The main script body that validates parameters and calls the other functions in the correct order.

### 3.2. Function Reference

Here is a summary of the key functions within the script:

| Function                      | Description                                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| `Write-Log`                   | Writes a formatted message to the console and the log file.                                             |
| `Initialize-Logging`          | Sets up the log file and transcript paths.                                                              |
| `Test-IsAdmin`                | Checks if the script is running with Administrator privileges.                                          |
| `Test-IPv4Address`            | Validates if a string is a valid IPv4 address.                                                          |
| `Convert-SubnetMaskToPrefixLength` | Converts a subnet mask (e.g., 255.255.255.0) to a CIDR prefix length (e.g., 24).                    |
| `Get-PrimaryInterface`        | Finds the primary network adapter.                                                                      |
| `Import-AnswerFile`           | Reads and parses a JSON or CSV answer file.                                                             |
| `Set-SystemConfig`            | Sets the computer hostname and time zone.                                                               |
| `Set-NetworkConfig`           | Configures the IP address, subnet, gateway, and DNS servers for the primary network adapter.          |
| `Invoke-InstallWindowsFeature`| Installs specified Windows roles/features, handling PowerShell 7 compatibility.                         |
| `Configure-IISPostInstall`    | Creates a default IIS web page and enables firewall rules.                                              |
| `Configure-DNSPostInstall`    | Creates a DNS zone and records.                                                                         |
| `Install-ServerRoles`         | Orchestrates the installation of roles and calls the appropriate post-configuration functions.            |
| `Configure-WSUSPolicy`        | Configures registry keys to point the server to a WSUS server.                                          |
| `Invoke-WindowsUpdate`        | Checks for, downloads, and installs Windows updates.                                                    |
| `Invoke-RebootIfNeeded`       | Checks if a reboot is pending and restarts the computer unless suppressed.                              |

### 3.3. Testing Guide

The project includes Pester tests to validate the script's functions.

- **Test File:** `Setup-FabrikamServer-Extended.Tests.ps1`
- **To Run Tests:** Open a PowerShell console, navigate to the project directory, and run the following command:

```powershell
Invoke-Pester -Path .\Setup-FabrikamServer-Extended.Tests.ps1
```

The tests will validate the helper functions like `Convert-SubnetMaskToPrefixLength` and `Test-IPv4Address`, as well as the logic for importing answer files.

---

## 4. Test Results

This section should be updated with the output from the Pester tests after running them successfully.

*(Please paste the full output of the `Invoke-Pester` command here.)*

```
<PASTE TEST RESULTS HERE>
```
