' 老六 Chat — 狗都会双击安装
Option Explicit
Dim shell, fso, scriptDir, result, msg

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = scriptDir

' ---- 1. 安装 Python 依赖 ----
result = shell.Run("cmd /c pip install --quiet pillow PyPDF2 python-docx openpyxl python-pptx", 1, True)

If result = 0 Then
    msg = "[√] Python 依赖安装完成"
Else
    msg = "[×] Python 依赖安装失败 —— 请确认已安装 Python（python.org 下载），安装时勾选 'Add to PATH'"
    MsgBox msg, 48, "老六 Chat — 安装"
    Set shell = Nothing
    Set fso = Nothing
    WScript.Quit 1
End If

' ---- 2. 安装 Node.js 依赖 ----
result = shell.Run("cmd /c npm install", 1, True)

If result = 0 Then
    msg = msg & vbCrLf & "[√] Node.js 依赖安装完成"
Else
    msg = msg & vbCrLf & "[×] Node.js 依赖安装失败 —— 请确认已安装 Node.js（nodejs.org 下载）"
End If

msg = msg & vbCrLf & vbCrLf & "安装完成！现在双击 【狗都会双击启动nzc不会.vbs】 即可启动老六 Chat。"

MsgBox msg, 64, "老六 Chat — 安装完成"

Set shell = Nothing
Set fso = Nothing
