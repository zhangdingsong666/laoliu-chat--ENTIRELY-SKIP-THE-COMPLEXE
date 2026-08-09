param(
    [ValidateSet("getpos", "move", "click", "doubleclick", "rightclick", "drag")]
    [string]$Action = "getpos",
    [int]$X = 0,
    [int]$Y = 0
)

Add-Type -AssemblyName System.Windows.Forms

# P/Invoke for mouse_event
$signature = @'
[DllImport("user32.dll")]
public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);
[DllImport("user32.dll")]
public static extern bool SetCursorPos(int X, int Y);
[DllImport("user32.dll")]
public static extern bool GetCursorPos(out POINT lpPoint);

[StructLayout(LayoutKind.Sequential)]
public struct POINT {
    public int X;
    public int Y;
}
'@

$WinAPI = Add-Type -MemberDefinition $signature -Name "WinAPI" -Namespace "MouseControl" -PassThru

$MOUSEEVENTF_LEFTDOWN = 0x0002
$MOUSEEVENTF_LEFTUP = 0x0004
$MOUSEEVENTF_RIGHTDOWN = 0x0008
$MOUSEEVENTF_RIGHTUP = 0x0010
$MOUSEEVENTF_MOVE = 0x0001
$MOUSEEVENTF_ABSOLUTE = 0x8000

function Get-CursorPos {
    $point = New-Object MouseControl.WinAPI+POINT
    [MouseControl.WinAPI]::GetCursorPos([ref]$point)
    return @{ X = $point.X; Y = $point.Y }
}

function Move-Cursor {
    param([int]$X, [int]$Y, [int]$DurationMs = 200)
    [MouseControl.WinAPI]::SetCursorPos($X, $Y)
    Start-Sleep -Milliseconds $DurationMs
}

function Send-Click {
    [MouseControl.WinAPI]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    Start-Sleep -Milliseconds 50
    [MouseControl.WinAPI]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
}

function Send-DoubleClick {
    Send-Click
    Start-Sleep -Milliseconds 100
    Send-Click
}

function Send-RightClick {
    [MouseControl.WinAPI]::mouse_event($MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    Start-Sleep -Milliseconds 50
    [MouseControl.WinAPI]::mouse_event($MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
}

function Send-Drag {
    param([int]$TargetX, [int]$TargetY)
    $start = Get-CursorPos
    [MouseControl.WinAPI]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    Start-Sleep -Milliseconds 30

    # Smooth drag in steps
    $steps = 20
    for ($i = 1; $i -le $steps; $i++) {
        $cx = $start.X + ($TargetX - $start.X) * $i / $steps
        $cy = $start.Y + ($TargetY - $start.Y) * $i / $steps
        [MouseControl.WinAPI]::SetCursorPos([int]$cx, [int]$cy)
        Start-Sleep -Milliseconds 10
    }

    Start-Sleep -Milliseconds 50
    [MouseControl.WinAPI]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
}

switch ($Action) {
    "getpos" {
        $p = Get-CursorPos
        Write-Output "Mouse position: X=$($p.X), Y=$($p.Y)"
    }
    "move" {
        Move-Cursor -X $X -Y $Y
        Write-Output "Moved mouse to X=$X, Y=$Y"
    }
    "click" {
        Send-Click
        Write-Output "Left click"
    }
    "doubleclick" {
        Send-DoubleClick
        Write-Output "Double click"
    }
    "rightclick" {
        Send-RightClick
        Write-Output "Right click"
    }
    "drag" {
        Send-Drag -TargetX $X -TargetY $Y
        Write-Output "Dragged to X=$X, Y=$Y"
    }
}
