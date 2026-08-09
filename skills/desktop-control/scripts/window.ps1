param(
    [ValidateSet("list", "find", "focus", "minimize", "maximize")]
    [string]$Action = "list",
    [string]$Title = ""
)

$signature = @'
[DllImport("user32.dll")]
public static extern bool SetForegroundWindow(IntPtr hWnd);
[DllImport("user32.dll")]
public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")]
public static extern bool IsWindowVisible(IntPtr hWnd);
[DllImport("user32.dll")]
public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
[DllImport("user32.dll")]
public static extern int GetWindowTextLength(IntPtr hWnd);
'@

$WinAPI = Add-Type -MemberDefinition $signature -Name "WinAPI" -Namespace "WindowControl" -PassThru

$SW_MINIMIZE = 6
$SW_MAXIMIZE = 3
$SW_RESTORE = 9

function Get-WindowTitle($hWnd) {
    $len = [WindowControl.WinAPI]::GetWindowTextLength($hWnd)
    if ($len -gt 0) {
        $sb = New-Object System.Text.StringBuilder($len + 1)
        [WindowControl.WinAPI]::GetWindowText($hWnd, $sb, $sb.Capacity)
        return $sb.ToString()
    }
    return ""
}

switch ($Action) {
    "list" {
        Get-Process | Where-Object { $_.MainWindowTitle -ne "" } | Sort-Object MainWindowTitle | ForEach-Object {
            Write-Output "[$($_.Id)] $($_.ProcessName) - $($_.MainWindowTitle)"
        }
    }
    "find" {
        $results = Get-Process | Where-Object { $_.MainWindowTitle -like "*$Title*" -and $_.MainWindowTitle -ne "" }
        if ($results) {
            $results | ForEach-Object {
                Write-Output "[$($_.Id)] $($_.ProcessName) - $($_.MainWindowTitle)"
            }
        } else {
            Write-Output "No window found matching: $Title"
        }
    }
    "focus" {
        $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*$Title*" -and $_.MainWindowTitle -ne "" } | Select-Object -First 1
        if ($proc) {
            [WindowControl.WinAPI]::SetForegroundWindow($proc.MainWindowHandle)
            Write-Output "Focused: $($proc.MainWindowTitle)"
        } else {
            Write-Output "Window not found: $Title"
        }
    }
    "minimize" {
        $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*$Title*" -and $_.MainWindowTitle -ne "" } | Select-Object -First 1
        if ($proc) {
            [WindowControl.WinAPI]::ShowWindow($proc.MainWindowHandle, $SW_MINIMIZE)
            Write-Output "Minimized: $($proc.MainWindowTitle)"
        } else {
            Write-Output "Window not found: $Title"
        }
    }
    "maximize" {
        $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*$Title*" -and $_.MainWindowTitle -ne "" } | Select-Object -First 1
        if ($proc) {
            [WindowControl.WinAPI]::ShowWindow($proc.MainWindowHandle, $SW_MAXIMIZE)
            Write-Output "Maximized: $($proc.MainWindowTitle)"
        } else {
            Write-Output "Window not found: $Title"
        }
    }
}
