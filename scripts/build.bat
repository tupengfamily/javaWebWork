@echo off
REM =============================================================================
REM build.bat - Build Docker images (does not start them)
REM =============================================================================
REM Usage:
REM   build.bat                  # build all services
REM   build.bat backend frontend # build specific services
REM   build.bat --no-cache       # pass through extra flags
REM =============================================================================
cd /d "%~dp0\.."

where docker >nul 2>nul
if errorlevel 1 (
    echo Error: docker not found. Install Docker first.
    exit /b 1
)

echo [build] building images: %*
docker compose build %*
if errorlevel 1 exit /b 1
echo [build] done. Run scripts\start.bat to deploy.
