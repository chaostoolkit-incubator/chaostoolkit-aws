#Script for FillDisk Chaos Monkey


Param([parameter(mandatory=$true)] [int]$duration,
[parameter(mandatory=$true)] [int]$size)

Write-Host "Filling disk with $size MB of random data for $duration seconds."

$Msize = $size*1024000

fsutil file createnew C:/burn $Msize
Start-Sleep -s $duration
rm C:/burn