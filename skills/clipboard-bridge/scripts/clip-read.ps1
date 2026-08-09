# Read current clipboard text content
Add-Type -AssemblyName System.Windows.Forms

try {
    $text = [System.Windows.Forms.Clipboard]::GetText()
    if ($text) {
        Write-Output $text
    } else {
        Write-Output "[Clipboard is empty or contains non-text content]"
    }
} catch {
    Write-Output "[Error reading clipboard: $_]"
}
