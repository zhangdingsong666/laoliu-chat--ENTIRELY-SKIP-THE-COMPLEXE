@echo off
cd /d "%~dp0"

REM ---- Desktop shortcut (first run only) ----
if not exist "%USERPROFILE%\Desktop\LaoLiuChat.lnk" (
    powershell -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell;$s=$ws.CreateShortcut('%USERPROFILE%\Desktop\LaoLiuChat.lnk');$s.TargetPath='powershell.exe';$s.Arguments='-ExecutionPolicy Bypass -NoExit -File ''%~dp0“ªº¸∆Ù∂Ø.ps1''';$s.WorkingDirectory='%~dp0';$s.Description='LaoLiu Chat';if(Test-Path '%~dp0app-icon.ico'){$s.IconLocation='%~dp0app-icon.ico'};$s.Save()"
    echo Desktop shortcut created: LaoLiuChat
)

REM ---- Launch ----
start "" pythonw "%~dp0¿œ¡˘Chat.pyw"
echo LaoLiu Chat started!