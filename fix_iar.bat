@echo off
setlocal enabledelayedexpansion

REM fix_iar.bat
REM This script makes a FP copy of an IAR to "fixed.iar"
REM 2025 - Enhanced version with error handling and flexibility

echo.
echo ========================================
echo    OpenSim IAR Permission Fixer
echo ========================================
echo.

REM Check if filename provided
if "%~1" equ "" goto USAGE

REM Get the input filename and handle extensions
set "input_file=%~1"
set "input_name=%~n1"
set "input_ext=%~x1"

REM If no extension provided, assume .iar
if "!input_ext!" equ "" (
    set "input_file=%~1.iar"
    set "input_name=%~1"
)

REM Check if input file exists
if not exist "!input_file!" (
    echo ERROR: Input file "!input_file!" not found.
    echo.
    goto USAGE
)

REM Create output filename
set "output_file=!input_name!_fixed.iar"

echo Processing: !input_file!
echo Output:     !output_file!
echo.

REM Create temporary directory
echo [1/5] Creating temporary directory...
if exist "iartemp" (
    echo WARNING: iartemp directory already exists. Removing...
    rd /s /q "iartemp" 2>nul
    if errorlevel 1 (
        echo ERROR: Could not remove existing iartemp directory.
        goto CLEANUP
    )
)
md "iartemp" 2>nul
if errorlevel 1 (
    echo ERROR: Could not create temporary directory.
    goto CLEANUP
)

REM Extract IAR file
echo [2/5] Extracting IAR file...
tar zxf "!input_file!" -C "iartemp" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to extract IAR file. Check if file is valid.
    goto CLEANUP
)

REM Check if extraction was successful
if not exist "iartemp\archive.xml" (
    echo ERROR: Invalid IAR file - archive.xml not found after extraction.
    goto CLEANUP
)

REM Apply permissions
echo [3/5] Applying permissions...
call apply_perms.bat "iartemp" --no-confirm
if errorlevel 1 (
    echo ERROR: Failed to apply permissions.
    goto CLEANUP
)

REM Create new IAR file
echo [4/5] Creating new IAR file...
cd "iartemp" && tar zcf "..\!output_file!" archive.xml inventory/* assets/* 2>nul && cd ..
if errorlevel 1 (
    echo ERROR: Failed to create new IAR file.
    goto CLEANUP
)

REM Verify output file was created
if not exist "!output_file!" (
    echo ERROR: Output file was not created successfully.
    goto CLEANUP
)

REM Clean up
echo [5/5] Cleaning up...
rd /s /q "iartemp" 2>nul

echo.
echo ========================================
echo    SUCCESS: !output_file! created!
echo ========================================
echo.
goto END

:CLEANUP
echo.
echo ERROR: Operation failed. Cleaning up...
if exist "iartemp" (
    rd /s /q "iartemp" 2>nul
)
if exist "!output_file!" (
    del "!output_file!" 2>nul
)
echo.
goto END

:USAGE
echo Usage: fix_iar [filename]
echo.
echo Examples:
echo   fix_iar myfile.iar
echo   fix_iar myfile
echo   fix_iar "path\to\my file.iar"
echo.
echo The script will:
echo   1. Extract the IAR file
echo   2. Apply full permissions to all items
echo   3. Create a new IAR with "_fixed" suffix
echo   4. Clean up temporary files
echo.

:END
endlocal
