@echo off
REM =============================================================================
REM stop.bat - Stop the Docker stack
REM =============================================================================
REM Usage:
REM   stop.bat            REM docker compose down (keeps volumes)
REM   stop.bat --volumes  REM also delete MySQL data (DANGEROUS)
REM =============================================================================
cd /d "%~dp0\.."

if "%1"=="--volumes" goto :confirm_volumes
if "%1"=="-v" goto :confirm_volumes

:do_stop
echo [stop] stopping services...
docker compose down %*
if errorlevel 1 exit /b 1
echo [stop] done. Run scripts\start.bat to bring the stack back up.
goto :eof

:confirm_volumes
echo.
echo WARNING: --volumes will DELETE the MySQL data volume.
echo          All crawled rankings will be lost.
echo.
set /p ANS=Type 'yes' to confirm: 
if /i not "%ANS%"=="yes" (
    echo Aborted.
    exit /b 1
)
goto :do_stop
