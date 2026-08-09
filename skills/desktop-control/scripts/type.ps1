param(
    [string]$Text = "",
    [string]$Keys = ""
)

Add-Type -AssemblyName System.Windows.Forms

if ($Text) {
    # Use SendKeys for text input
    [System.Windows.Forms.SendKeys]::SendWait($Text)
    Write-Output "Typed: $Text"
}
elseif ($Keys) {
    [System.Windows.Forms.SendKeys]::SendWait($Keys)
    Write-Output "Sent keys: $Keys"
}
else {
    Write-Output "Usage: type.ps1 -Text 'text to type' OR type.ps1 -Keys '^c'"
}
