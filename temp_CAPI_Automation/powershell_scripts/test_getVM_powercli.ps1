#Connect-VIServer -Server 10.45.134.100 -Protocol https -User root -Password intel@123
#Connect-VIServer 10.45.134.100 -user root -password intel@123
#Add-Type –Path "/shared_data/drivers.io.vmware.validation.test-automation-framework/Testcases/Platform/config_ps.txt"
Param(
   [Parameter(Position=1)]
   [string]$ESXHost,
   
   [Parameter(Position=2)]
   [string]$usr,

   [Parameter(Position=3)]
   [string]$pwd,

   [Parameter(Position=4)]
   [string]$VM_name,

   [Parameter(Position=5)]
   [string]$coreperscok,

   [Parameter(Position=6)]
   [string]$cpus
   
)
 
# parameter as first input
write-Host "host IP address:          "  $ESXHost

# paramter as second input
Write-Host "user name:     "  $usr
# paramter as third input
Write-Host "password:     "  $pwd

# paramter as 4th input
Write-Host "vmname:     "  $VM_name
# paramter as 5th input
Write-Host "Corespersocket:     "  $coreperscok
# paramter as 6th input
Write-Host "no of Cpus:     "  $cpus
#$ESXHost="10.45.134.100"

Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false
Connect-VIServer $ESXHost -user $usr -password $pwd 

#Get-VMhost $ESXHost | Get-VM | FT

Write-Host "Corespersocket value before applying:     "  $coreperscok
# paramter as 6th input
Write-Host "no of Cpus value before appying:     "  $cpus

$VM=Get-VM -Name $VM_name
Write-Host " command coreper scok " New-Object -Type VMware.Vim.VirtualMachineConfigSpec -Property @{ "NumCoresPerSocket" = $coreperscok}

$VMSpec=New-Object -Type VMware.Vim.VirtualMachineConfigSpec -Property @{ "NumCoresPerSocket" = $coreperscok}
Start-Sleep -Seconds 5
$VM.ExtensionData.ReconfigVM_Task($VMSpec)
Write-Host " command for no of cpus " Set-VM -NumCPU $cpus
Start-Sleep -Seconds 5
$VM | Set-VM -NumCPU $cpus -Confirm:$false
Start-Sleep -Seconds 5
