:: build.bat for LoreMaster plugin
@echo off
setlocal

:: Change to the parent directory (project root)
cd /d "%~dp0\.."

:: Try python first
where /q python
if ERRORLEVEL 1 goto python3
set PYTHON=python
goto build

:python3
where /q python3
if ERRORLEVEL 1 goto nopython
set PYTHON=python3

:build
set VENV=.venv
set DIST_DIR=dist
set PLUGIN_NAME=loremaster
set PLUGIN_DIR=%DIST_DIR%\%PLUGIN_NAME%

if exist %VENV% (
    call %VENV%\Scripts\activate.bat

    if not exist "%PLUGIN_DIR%" mkdir "%PLUGIN_DIR%"

    pyinstaller --onefile --name g-assist-plugin-%PLUGIN_NAME% --distpath "%PLUGIN_DIR%" plugin.py

    if exist manifest.json (
        copy /y manifest.json "%PLUGIN_DIR%\manifest.json"
    ) 
    if exist config.json (
        copy /y config.json "%PLUGIN_DIR%\config.json"
    )

    call %VENV%\Scripts\deactivate.bat
    echo ✅ Build complete. Executable in "%PLUGIN_DIR%"
    exit /b 0
) else (
    echo ❌ Please run setup.bat to create the venv
    exit /b 1
)

:nopython
echo ❌ Python must be installed and in PATH
exit /b 1
