param(
    [Parameter(Mandatory=$true)]
    [string]$Text
)

Add-Type -AssemblyName System.Windows.Forms

try {
    [System.Windows.Forms.Clipboard]::SetText($Text)
    Write-Output "Clipboard set: $($Text.Substring(0, [Math]::Min(50, $Text.Length)))..."
} catch {
    Write-Output "[Error writing to clipboard: $_]"
}
