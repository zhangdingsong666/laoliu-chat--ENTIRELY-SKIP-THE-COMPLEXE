@echo off
chcp 65001 >nul
title 老六 Chat - 桌面助手
cd /d "%~dp0"
start "" pythonw.exe "%~dp0老六Chat.pyw"
