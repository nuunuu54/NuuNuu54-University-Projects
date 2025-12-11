# Setup-FabrikamServer-Extended.Tests.ps1

Describe 'Setup-FabrikamServer-Extended Function Tests' {
    # Mock the Write-Log function to suppress output during tests
    function Write-Log { }

    # Define a dummy Test-IsAdmin function that always returns true
    # This function will be present in the session before the main script is sourced
    # preventing the "This script must be run as an Administrator" error.
    function Test-IsAdmin { return $true }
    
    BeforeAll {
        # Set a flag to prevent the main script from executing when sourced for testing.
        $global:IsTestMode = $true
        # Import the functions to test. Write-Log and Test-IsAdmin are mocked in the Describe scope.
        . "$PSScriptRoot\Setup-FabrikamServer-Extended.ps1"
    }
    Context 'Convert-SubnetMaskToPrefixLength' {
        It 'should convert a valid subnet mask to a prefix length' {
            $prefix = Convert-SubnetMaskToPrefixLength -Mask '255.255.255.0'
            $prefix | Should Be 24
        }

        It 'should throw an error for an invalid subnet mask' {
            { Convert-SubnetMaskToPrefixLength -Mask '255.255.0' } | Should Throw
        }
    }

    Context 'Test-IPv4Address' {
        It 'should return true for a valid IPv4 address' {
            $valid = Test-IPv4Address -Address '192.168.1.1'
            $valid | Should Be $true
        }

        It 'should return false for an invalid IPv4 address' {
            $invalid = Test-IPv4Address -Address '192.168.1.256'
            $invalid | Should Be $false
        }

        It 'should return false for 0.0.0.0' {
            $invalid = Test-IPv4Address -Address '0.0.0.0'
            $invalid | Should Be $false
        }

        It 'should return false for 255.255.255.255' {
            $invalid = Test-IPv4Address -Address '255.255.255.255'
            $invalid | Should Be $false
        }
    }

    Context 'Get-PrimaryInterface' {
        BeforeAll {
            # Mock Get-NetAdapter
            Mock -CommandName Get-NetAdapter {
                param($Name)
                $mockNics = @(
                    [pscustomobject]@{ Name = 'Ethernet'; Status = 'Up'; ifIndex = 1 }
                    [pscustomobject]@{ Name = 'Wi-Fi'; Status = 'Up'; ifIndex = 2 }
                    [pscustomobject]@{ Name = 'Bluetooth'; Status = 'Down'; ifIndex = 3 }
                )
                if ($Name) {
                    return $mockNics | Where-Object { $_.Name -eq $Name }
                }
                return $mockNics
            }
        }

        It 'should return the first "Up" interface' {
            $interface = Get-PrimaryInterface
            $interface | Should Be 'Ethernet'
        }

        It 'should return the specified interface if it exists and is "Up"' {
            $interface = Get-PrimaryInterface -Alias 'Wi-Fi'
            $interface | Should Be 'Wi-Fi'
        }

        It 'should throw an error if the specified interface does not exist' {
            { Get-PrimaryInterface -Alias 'non-existent' } | Should Throw "Interface 'non-existent' not found."
        }
    }

    Context 'Import-AnswerFile' {
        BeforeAll {
            # Create dummy answer files
            $json = @{
                Hostname = 'FAB-TEST-01'
                IpAddress = '10.0.0.100'
            } | ConvertTo-Json
            $json | Out-File -FilePath 'test.json' -Encoding utf8
		}

		AfterAll {
			# Remove dummy files
			Remove-Item -Path 'test.json' -ErrorAction SilentlyContinue
			# test.csv is now a permanent file and should not be removed
		}

        It 'should import a JSON answer file' {
            $config = Import-AnswerFile -Path 'test.json'
            $config.Hostname | Should Be 'FAB-TEST-01'
            $config.IpAddress | Should Be '10.0.0.100'
        }

        It 'should import a CSV answer file' {
            $csvPath = 'dummy.csv'
            @"
Hostname,IpAddress
FAB-TEST-02,10.0.0.101
"@ | Out-File -FilePath $csvPath -Encoding utf8
            try {
                $config = Import-AnswerFile -Path $csvPath
                $config.Hostname | Should Be 'FAB-TEST-02'
                $config.IpAddress | Should Be '10.0.0.101'
            } finally {
                Remove-Item -Path $csvPath -ErrorAction SilentlyContinue
            }
        }

        It 'should throw an error for an unsupported file type' {
            { Import-AnswerFile -Path 'README.md' } | Should Throw
        }
    }

    Context 'DryRun' {
        BeforeEach {
            # Enable dry-run and capture Write-Log output
            $script:DryRun = $true
            $script:Captured = @()
            Mock -CommandName Write-Log -MockWith { param($Message,$Level='INFO') $script:Captured += $Message }
        }

        It 'should report planned actions for system configuration' {
            Set-SystemConfig -NewHostname 'DRY-HOST' -TimeZoneId 'UTC'
            ($script:Captured -join "`n") | Should Match 'DRY-RUN'
        }

        It 'should report planned actions for feature installation' {
            Invoke-InstallWindowsFeature -Name 'Web-Server'
            ($script:Captured -join "`n") | Should Match 'DRY-RUN'
        }
    }
}
