@echo off
REM OpenSim IAR Full Permissions Batch Script
REM ==========================================
REM
REM This batch file provides easy commands for applying full permissions
REM to OpenSim IAR XML files.
REM
REM Usage examples:
REM   apply_perms.bat new
REM   apply_perms.bat new --backup
REM   apply_perms.bat new --max-perms
REM   apply_perms.bat new --test

if "%1"=="" goto usage
if "%1"=="help" goto usage
if "%1"=="--help" goto usage
if "%1"=="-h" goto usage

set FOLDER=%1
shift

REM Check if it's a special command
if "%FOLDER%"=="test" (
    set FOLDER=%2
    shift
    set PERM_ARGS=--standard --dry-run --no-confirm
) else if "%FOLDER%"=="max" (
    set FOLDER=%2
    shift
    set PERM_ARGS=--max-perms --no-confirm
) else (
    REM Default to standard permissions (with confirmation)
    set PERM_ARGS=--standard
)

echo Applying standard full permissions to IAR files in '%FOLDER%'...
python apply_full_perms.py %PERM_ARGS% %FOLDER% %1 %2 %3 %4 %5 %6 %7 %8

goto end

:usage
echo.
echo OpenSim IAR Full Permissions Tool
echo =================================
echo.
echo Usage: apply_perms.bat [folder] [options]
echo        apply_perms.bat test [folder] [options]
echo        apply_perms.bat max [folder] [options]
echo.
echo Default behavior:
echo   - Uses standard full permissions (581639)
echo   - Processes subdirectories recursively
echo   - Asks for confirmation before applying
echo.
echo Examples:
echo   apply_perms.bat new
echo   apply_perms.bat new --backup
echo   apply_perms.bat test new
echo   apply_perms.bat max new --no-confirm
echo.
echo Options: --backup --no-confirm --verbose
echo.

:end 
