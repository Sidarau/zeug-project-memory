@echo off
rem zm for Windows (cmd and PowerShell). Runs zm.ps1 whatever the execution policy is.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0zm.ps1" %*
