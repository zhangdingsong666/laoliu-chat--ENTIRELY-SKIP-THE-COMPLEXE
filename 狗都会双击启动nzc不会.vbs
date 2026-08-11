' LaoLiu Chat - Launch (double-click to run)
Option Explicit
Dim shell, fso, scriptDir, desktop, shortcutPath

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

' ---- Desktop shortcut (first run only) ----
desktop = shell.SpecialFolders("Desktop")
shortcutPath = desktop & "\LaoLiuChat.lnk"

If Not fso.FileExists(shortcutPath) Then
    On Error Resume Next
    Dim sc
    Set sc = shell.CreateShortcut(shortcutPath)
    sc.TargetPath = "powershell.exe"
    sc.Arguments = "-ExecutionPolicy Bypass -NoExit -File """ & scriptDir & "\一键启动.ps1"""
    sc.WorkingDirectory = scriptDir
    sc.Description = "LaoLiu Chat"
    If fso.FileExists(scriptDir & "\app-icon.ico") Then
        sc.IconLocation = scriptDir & "\app-icon.ico"
    End If
    sc.Save()
    On Error Goto 0
End If

' ---- Launch ----
If Not fso.FileExists(scriptDir & "\老六Chat.pyw") Then
    MsgBox "Cannot find LaoLiuChat.pyw - please extract all files first", 48, "LaoLiu Chat"
    WScript.Quit 1
End If

shell.Run "pythonw """ & scriptDir & "\老六Chat.pyw""", 0, False

Set shell = Nothing
Set fso = Nothing