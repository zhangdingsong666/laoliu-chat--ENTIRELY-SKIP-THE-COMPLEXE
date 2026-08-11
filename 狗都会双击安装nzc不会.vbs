' LaoLiu Chat - Install (double-click to run)
Option Explicit
Dim shell, fso, scriptDir, result, msg

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

' ---- 1. Python deps ----
result = shell.Run("cmd /c pip install --quiet pillow PyPDF2 python-docx openpyxl python-pptx", 1, True)

If result = 0 Then
    msg = "[OK] Python dependencies installed"
Else
    msg = "[FAIL] Python deps failed - install Python from python.org (check 'Add to PATH')"
    MsgBox msg, 48, "LaoLiu Chat - Install"
    Set shell = Nothing
    Set fso = Nothing
    WScript.Quit 1
End If

' ---- 2. Node.js deps ----
result = shell.Run("cmd /c npm install", 1, True)

If result = 0 Then
    msg = msg & vbCrLf & "[OK] Node.js dependencies installed"
Else
    msg = msg & vbCrLf & "[FAIL] Node.js deps failed - install Node.js from nodejs.org"
End If

msg = msg & vbCrLf & vbCrLf & "All done! Now double-click the START vbs file to launch LaoLiu Chat."

MsgBox msg, 64, "LaoLiu Chat - Done"

Set shell = Nothing
Set fso = Nothing