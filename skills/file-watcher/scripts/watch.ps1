param(
    [Parameter(Mandatory=$true)]
    [string]$Path,
    [string]$Filter = "*.*",
    [int]$DurationSeconds = 30,
    [switch]$IncludeSubdirs
)

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $Path
$watcher.Filter = $Filter
$watcher.IncludeSubdirectories = $IncludeSubdirs
$watcher.EnableRaisingEvents = $true

$startTime = Get-Date
$endTime = $startTime.AddSeconds($DurationSeconds)

Write-Output "Watching: $Path"
Write-Output "Filter: $Filter"
Write-Output "Duration: ${DurationSeconds}s"
Write-Output "Include subdirs: $IncludeSubdirs"
Write-Output "---"

# Register event handlers
$action = {
    $event = $Event.SourceEventArgs
    $changeType = $Event.SourceEventArgs.ChangeType
    $fullPath = $Event.SourceEventArgs.FullPath
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    Write-Output "[$timestamp] $changeType`: $fullPath"
}

$handlers = @()
$handlers += Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action
$handlers += Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $action
$handlers += Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $action
$handlers += Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $action

try {
    while ((Get-Date) -lt $endTime) {
        Start-Sleep -Milliseconds 500
    }
} finally {
    foreach ($handler in $handlers) {
        Unregister-Event -SubscriptionId $handler.Id -ErrorAction SilentlyContinue
    }
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
}

Write-Output "---"
Write-Output "Watch completed."
