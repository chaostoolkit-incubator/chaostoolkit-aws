Param([parameter(mandatory=$true)] [int]$duration)

$CPUs = (Get-WMIObject win32_processor | Measure-Object NumberofLogicalProcessors -sum).sum
Write-Output "Stressing $Cpus CPUs for $duration seconds."

ForEach ($Number in 1..$CPUs){
    Start-Job -ScriptBlock{
        param ($duration)
        $stopwatch =  [system.diagnostics.stopwatch]::StartNew()
        $result = 1;
        while ($stopwatch.Elapsed.TotalSeconds -lt $duration) {
            $result = $result * $number
        }
    } -Arg $duration

}

Get-Job | Wait-Job