@
echo Starting Windows optimization script...
echo ==========================================

powershell -ExecutionPolicy Bypass -NoProfile -File "WindowsOptimizer.ps1"

echo ==========================================
echo Optimization script completed.
pause
echo off
chcp 65001 >nul
title Starting optimization Windows

REM text text administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo text to run text text administrator.
    echo Please, run text text text administrator.
    pause
    exit
)

REM text text file script
if not exist "WindowsOptimizer.ps1" (
    echo text text file WindowsOptimizer.ps1
    echo Make sure, text file located text text text folder, text text this .bat file.
    pause
    exit
)

REM text text PS1 file text text UTF-8
set "tempFile=%temp%\WindowsOptimizer-%random%.ps1"
type "WindowsOptimizer.ps1" > "%tempFile%" || (
    echo text text text text file script.
    pause
    exit
)

REM Starting PowerShell script text text text completed text text text
powershell -ExecutionPolicy Bypass -NoProfile -File "%tempFile%" -Encoding UTF8

REM text text file script
if exist "%tempFile%" del /f /q "%tempFile%"

pause
 >nul 2>&1