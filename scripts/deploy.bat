@echo off
echo Deploying LoreMaster plugin to G-Assist...

REM Store the original directory and change to project root
set "ORIGINAL_DIR=%~dp0\.."

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges.
    goto :deploy
) else (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -ArgumentList '%ORIGINAL_DIR%' -Verb RunAs"
    exit /b
)

:deploy
REM If argument provided, use it as the working directory, otherwise use project root
if not "%~1"=="" (
    cd /d "%~1"
    echo Changed directory to: %~1
) else (
    cd /d "%ORIGINAL_DIR%"
    echo Changed directory to project root: %ORIGINAL_DIR%
)

REM Check if dist\loremaster exists
if not exist "dist\loremaster" (
    echo ✗ Error: dist\loremaster directory not found!
    echo ✗ Make sure you've run build.bat first and you're in the correct directory.
    echo Current directory: %CD%
    goto :error
)

echo Copying plugin files to G-Assist plugins directory...
echo Source: %CD%\dist\loremaster
echo Destination: %PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins\loremaster

xcopy "dist\loremaster" "%PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins\loremaster" /E /I /Y

if %errorLevel% == 0 (
    echo.
    echo ✓ Plugin deployed successfully!
    echo ✓ Files copied to: %PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins\loremaster
    echo ✓ Restart G-Assist to enable the plugin.
) else (
    echo.
    echo ✗ Deployment failed with error code %errorLevel%
    goto :error
)

echo.
pause
exit /b 0

:error
echo.
echo Troubleshooting:
echo 1. Make sure you've run build.bat first
echo 2. Run deploy.bat from the project root directory
echo 3. Check that dist\loremaster contains the plugin files
echo.
pause
exit /b 1