param(
    [ValidateSet("full", "screen", "region", "window")]
    [string]$Mode = "full",
    [int]$Index = 0,
    [int]$X = 0,
    [int]$Y = 0,
    [int]$Width = 500,
    [int]$Height = 300,
    [string]$OutputDir = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Default output: workspace/screenshots
# Use relative path from script to avoid encoding issues with Chinese chars in PS 5.1
if (-not $OutputDir) {
    $OutputDir = Join-Path $PSScriptRoot "..\..\..\screenshots"
    $OutputDir = [System.IO.Path]::GetFullPath($OutputDir)
}

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$filename = "screenshot-$Mode-$timestamp.png"
$filepath = Join-Path $OutputDir $filename

# Get screen bounds
$screens = [System.Windows.Forms.Screen]::AllScreens
$primaryScreen = [System.Windows.Forms.Screen]::PrimaryScreen

switch ($Mode) {
    "full" {
        # Get bounds covering all screens
        $minX = ($screens | ForEach-Object { $_.Bounds.X } | Measure-Object -Minimum).Minimum
        $minY = ($screens | ForEach-Object { $_.Bounds.Y } | Measure-Object -Minimum).Minimum
        $maxX = ($screens | ForEach-Object { $_.Bounds.X + $_.Bounds.Width } | Measure-Object -Maximum).Maximum
        $maxY = ($screens | ForEach-Object { $_.Bounds.Y + $_.Bounds.Height } | Measure-Object -Maximum).Maximum

        $totalWidth = [Math]::Max(1, $maxX - $minX)
        $totalHeight = [Math]::Max(1, $maxY - $minY)

        # Fallback: if dimensions are invalid, use primary screen
        try {
            $bitmap = New-Object System.Drawing.Bitmap($totalWidth, $totalHeight)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($minX, $minY, 0, 0, (New-Object System.Drawing.Size($totalWidth, $totalHeight)))
        } catch {
            # Fallback to primary screen
            $totalWidth = $primaryScreen.Bounds.Width
            $totalHeight = $primaryScreen.Bounds.Height
            $bitmap = New-Object System.Drawing.Bitmap($totalWidth, $totalHeight)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($primaryScreen.Bounds.X, $primaryScreen.Bounds.Y, 0, 0, $primaryScreen.Bounds.Size)
        }
    }
    "screen" {
        if ($Index -ge $screens.Count) { $Index = 0 }
        $screen = $screens[$Index]
        $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Bounds.X, $screen.Bounds.Y, 0, 0, $screen.Bounds.Size)
    }
    "region" {
        $bitmap = New-Object System.Drawing.Bitmap($Width, $Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($X, $Y, 0, 0, (New-Object System.Drawing.Size($Width, $Height)))
    }
    "window" {
        # Capture the foreground window by simulating Alt+PrintScreen
        # Fall back to full primary screen capture
        $bitmap = New-Object System.Drawing.Bitmap($primaryScreen.Bounds.Width, $primaryScreen.Bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($primaryScreen.Bounds.X, $primaryScreen.Bounds.Y, 0, 0, $primaryScreen.Bounds.Size)

        # Also try to get the active window title for context
        Add-Type @'
[DllImport("user32.dll")]
public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")]
public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
'@
        $hwnd = [GetForegroundWindow]
        $sb = New-Object System.Text.StringBuilder(256)
        [GetWindowText]::Invoke($hwnd, $sb, 256)
        $windowTitle = $sb.ToString()
        Write-Output "Active window: $windowTitle"
    }
}

# Save as PNG
$bitmap.Save($filepath, [System.Drawing.Imaging.ImageFormat]::Png)

# Cleanup
$graphics.Dispose()
$bitmap.Dispose()

# Output the file path for the agent to read
Write-Output "Screenshot saved: $filepath"

# Return the path so the agent can use it
$filepath
