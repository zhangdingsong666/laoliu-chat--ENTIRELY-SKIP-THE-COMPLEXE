Option Explicit
Dim shell, fso, scriptDir, msg, result
Dim pythonExe, pipExe, nodeExe, npmExe, winget

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

msg = "===== LaoLiu Chat - Full Install =====" & vbCrLf & vbCrLf

' ---- Check winget ----
winget = ""
If fso.FileExists("C:\Windows\System32\winget.exe") Then
    winget = "C:\Windows\System32\winget.exe"
End If

' ---- STEP 1: Find or install Python ----
pythonExe = FindInPaths(Array( _
    "python.exe", _
    "%LocalAppData%\Programs\Python\Python313\python.exe", _
    "%LocalAppData%\Programs\Python\Python312\python.exe", _
    "%LocalAppData%\Programs\Python\Python311\python.exe", _
    "%LocalAppData%\Programs\Python\Python310\python.exe", _
    "%ProgramFiles%\Python313\python.exe", _
    "%ProgramFiles%\Python312\python.exe", _
    "%ProgramFiles%\Python311\python.exe", _
    "C:\Python313\python.exe", _
    "C:\Python312\python.exe" _
))

If pythonExe = "" And winget <> "" Then
    msg = msg & "[..] Installing Python 3.12 (this may take a few minutes)..." & vbCrLf
    shell.Run "cmd /c " & winget & " install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements", 1, True
    pythonExe = FindInPaths(Array( _
        "%LocalAppData%\Programs\Python\Python312\python.exe", _
        "%LocalAppData%\Programs\Python\Python313\python.exe", _
        "%ProgramFiles%\Python312\python.exe", _
        "python.exe" _
    ))
End If

If pythonExe <> "" Then
    msg = msg & "[OK] Python: " & pythonExe & vbCrLf
Else
    msg = msg & "[FAIL] Python not found and cannot auto-install." & vbCrLf
    msg = msg & "Please download: https://python.org (CHECK 'Add to PATH')" & vbCrLf
    MsgBox msg, 48, "LaoLiu Chat - Install"
    WScript.Quit 1
End If

' ---- Find pip ----
pipExe = ""
Dim pyDir
pyDir = fso.GetParentFolderName(pythonExe)
If fso.FileExists(pyDir & "\Scripts\pip.exe") Then
    pipExe = pyDir & "\Scripts\pip.exe"
ElseIf fso.FileExists(pyDir & "\Scripts\pip3.exe") Then
    pipExe = pyDir & "\Scripts\pip3.exe"
Else
    pipExe = FindInPaths(Array("pip.exe", "pip3.exe", _
        "%LocalAppData%\Programs\Python\Python312\Scripts\pip.exe", _
        "%LocalAppData%\Programs\Python\Python313\Scripts\pip.exe"))
End If

If pipExe = "" Then
    msg = msg & "[FAIL] pip not found" & vbCrLf
    MsgBox msg, 48, "LaoLiu Chat - Install"
    WScript.Quit 1
End If

' ---- STEP 2: pip install ----
msg = msg & "[..] Installing Python packages..."
result = shell.Run("cmd /c """ & pipExe & """ install --quiet pillow PyPDF2 python-docx openpyxl python-pptx", 1, True)
If result = 0 Then
    msg = msg & " [OK]" & vbCrLf
Else
    msg = msg & " [WARN] some packages may have failed" & vbCrLf
End If

' ---- STEP 3: Find or install Node.js ----
nodeExe = FindInPaths(Array( _
    "%ProgramFiles%\nodejs\node.exe", _
    "%ProgramFiles(x86)%\nodejs\node.exe" _
))

If nodeExe = "" And winget <> "" Then
    msg = msg & "[..] Installing Node.js (this may take a few minutes)..." & vbCrLf
    shell.Run "cmd /c " & winget & " install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements", 1, True
    nodeExe = FindInPaths(Array("%ProgramFiles%\nodejs\node.exe", "%ProgramFiles(x86)%\nodejs\node.exe"))
End If

If nodeExe <> "" Then
    msg = msg & "[OK] Node.js: " & nodeExe & vbCrLf
Else
    msg = msg & "[SKIP] Node.js not found - red mode will not work" & vbCrLf
End If

' ---- Find npm ----
npmExe = ""
If nodeExe <> "" Then
    Dim nodeDir
    nodeDir = fso.GetParentFolderName(nodeExe)
    If fso.FileExists(nodeDir & "\npm.cmd") Then npmExe = nodeDir & "\npm.cmd"
End If
If npmExe = "" Then npmExe = FindInPaths(Array("%ProgramFiles%\nodejs\npm.cmd"))

' ---- STEP 4: npm install ----
If npmExe <> "" Then
    msg = msg & "[..] Installing Node.js packages..."
    result = shell.Run("cmd /c cd /d """ & scriptDir & """ && """ & npmExe & """ install --no-audit --no-fund", 1, True)
    If result = 0 Then
        msg = msg & " [OK]" & vbCrLf
    Else
        msg = msg & " [WARN] some packages may have failed" & vbCrLf
    End If
Else
    msg = msg & "[SKIP] npm not found" & vbCrLf
End If

' ---- Done ----
msg = msg & vbCrLf & "===== ALL DONE =====" & vbCrLf
msg = msg & "Now double-click the LAUNCH vbs file to start!" & vbCrLf
MsgBox msg, 64, "LaoLiu Chat - Install Complete"

Set shell = Nothing
Set fso = Nothing

' =============================================
' Helper: find first existing file from a list of paths
' =============================================
Function FindInPaths(pathList)
    Dim i, p
    For i = 0 To UBound(pathList)
        p = shell.ExpandEnvironmentStrings(pathList(i))
        If fso.FileExists(p) Then
            FindInPaths = p
            Exit Function
        End If
    Next
    FindInPaths = ""
End Function