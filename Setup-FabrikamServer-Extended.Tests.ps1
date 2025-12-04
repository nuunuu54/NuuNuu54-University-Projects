# Setup-FabrikamServer-Extended.Tests.ps1

# Mock the Write-Log function to suppress output during tests
function Write-Log { }

# Import the functions to test
. C:\Users\NuuNuu\Desktop\Yeah I code\Server-Admin-Work\Setup-FabrikamServer-Extended.ps1

Describe 'Setup-FabrikamServer-Extended Function Tests' {
    Context 'Convert-SubnetMaskToPrefixLength' {
        It 'should convert a valid subnet mask to a prefix length' {
            $prefix = Convert-SubnetMaskToPrefixLength -Mask '255.255.255.0'
            $prefix | Should -Be 24
        }

        It 'should throw an error for an invalid subnet mask' {
            { Convert-SubnetMaskToPrefixLength -Mask '255.255.0' } | Should -Throw
        }
    }

    Context 'Test-IPv4Address' {
        It 'should return true for a valid IPv4 address' {
            $valid = Test-IPv4Address -Address '192.168.1.1'
            $valid | Should -Be $true
        }

        It 'should return false for an invalid IPv4 address' {
            $invalid = Test-IPv4Address -Address '192.168.1.256'
            $invalid | Should -Be $false
        }

        It 'should return false for 0.0.0.0' {
            $invalid = Test-IPv4Address -Address '0.0.0.0'
            $invalid | Should -Be $false
        }

        It 'should return false for 255.255.255.255' {
            $invalid = Test-IPv4Address -Address '255.255.255.255'
            $invalid | Should -Be $false
        }
    }
}
