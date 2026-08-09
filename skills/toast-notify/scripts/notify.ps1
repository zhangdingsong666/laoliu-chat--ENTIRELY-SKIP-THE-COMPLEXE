param(
    [Parameter(Mandatory=$true)]
    [string]$Title,
    [Parameter(Mandatory=$true)]
    [string]$Message
)

# Windows 10/11 Toast Notification via .NET
Add-Type -AssemblyName System.Windows.Forms

# Load the Windows.UI.Notifications API
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

# Create toast XML template
$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>$Title</text>
            <text>$Message</text>
        </binding>
    </visual>
</toast>
"@

# Escape XML special chars in title and message
$escapedTitle = [System.Security.SecurityElement]::Escape($Title)
$escapedMessage = [System.Security.SecurityElement]::Escape($Message)

$toastXml = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>$escapedTitle</text>
            <text>$escapedMessage</text>
        </binding>
    </visual>
</toast>
"@

try {
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($toastXml)

    $appId = "OpenClaw.Agent"
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)

    Write-Output "Notification sent: $Title"
} catch {
    # Fallback: use .NET MessageBox-style notification via PowerShell
    Write-Output "Toast API failed, trying fallback..."
    try {
        $wshell = New-Object -ComObject Wscript.Shell
        $result = $wshell.Popup($Message, 0, $Title, 0x40)
        Write-Output "Fallback popup shown: $Title"
    } catch {
        Write-Output "Notification failed: $_"
    }
}
