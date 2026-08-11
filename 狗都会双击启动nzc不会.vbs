' 老六 Chat — 狗都会双击启动
Option Explicit
Dim shell, fso, scriptDir, desktop, shortcutPath, ps1Path

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

' ---- 桌面快捷方式（首次运行自动创建）----
desktop = shell.SpecialFolders("Desktop")
shortcutPath = desktop & "\老六Chat.lnk"

If Not fso.FileExists(shortcutPath) Then
    On Error Resume Next
    Dim sc
    Set sc = shell.CreateShortcut(shortcutPath)
    sc.TargetPath = "powershell.exe"
    sc.Arguments = "-ExecutionPolicy Bypass -NoExit -File """ & scriptDir & "\一键启动.ps1"""
    sc.WorkingDirectory = scriptDir
    sc.Description = "老六 Chat - AI 桌面助手"
    If fso.FileExists(scriptDir & "\app-icon.ico") Then
        sc.IconLocation = scriptDir & "\app-icon.ico"
    End If
    sc.Save()
    On Error Goto 0
End If

' ---- 启动程序 ----
If Not fso.FileExists(scriptDir & "\老六Chat.pyw") Then
    MsgBox "找不到 老六Chat.pyw，请确认解压完整", 48, "老六 Chat"
    WScript.Quit 1
End If

' 静默启动（不显示窗口）
shell.Run "pythonw """ & scriptDir & "\老六Chat.pyw""", 0, False

Set shell = Nothing
Set fso = Nothing
