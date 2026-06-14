@echo off
REM =============================================================================
REM dev.bat - Local dev mode (no Docker)
REM =============================================================================
REM Usage:
REM   dev.bat start    [backend|crawler|frontend|all]  (default: all)
REM   dev.bat stop     [backend|crawler|frontend|all]  (default: all)
REM   dev.bat status
REM   dev.bat restart  [target]
REM   dev.bat logs     [backend|crawler|frontend]
REM =============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0\.."
if not exist logs mkdir logs
if not exist .pids mkdir .pids

set "CMD=%1"
set "TARGET=%2"
if "%CMD%"=="" set "CMD=status"
if "%TARGET%"=="" set "TARGET=all"

REM --- find java 17 ---
set "JAVA=java"
if exist "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\bin\java.exe" (
    set "JAVA=C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\bin\java.exe"
)
if defined JAVA_HOME if exist "%JAVA_HOME%\bin\java.exe" set "JAVA=%JAVA_HOME%\bin\java.exe"

if "%CMD%"=="start" goto :do_start
if "%CMD%"=="stop" goto :do_stop
if "%CMD%"=="status" goto :do_status
if "%CMD%"=="restart" (
    call "%~dp0dev.bat" stop %TARGET%
    call "%~dp0dev.bat" start %TARGET%
    goto :eof
)
if "%CMD%"=="logs" goto :do_logs
echo Usage: dev.bat {start^|stop^|status^|restart^|logs} [target]
echo   target = backend^|crawler^|frontend^|all  (default: all)
goto :eof

:do_start
echo [dev] using: !JAVA!
echo [dev] starting: %TARGET%

REM --- backend ---
if /i "%TARGET%"=="all" goto :start_backend
if /i "%TARGET%"=="backend" goto :start_backend
goto :start_crawler

:start_backend
if not exist "backend\target\app.jar" (
    echo [dev] building backend...
    pushd backend
    call mvn -B clean package -DskipTests || (popd & exit /b 1)
    popd
)
echo [dev] starting backend on :8080
pushd backend
start "novel-backend" /B "" "!JAVA!" -XX:MaxRAMPercentage=75.0 -jar target\app.jar --spring.profiles.active=dev > "%~dp0..\logs\backend.log" 2>&1
popd

REM --- crawler ---
:start_crawler
if /i "%TARGET%"=="crawler" goto :do_start_crawler
if /i "%TARGET%"=="all" goto :do_start_crawler
goto :start_frontend

:do_start_crawler
echo [dev] starting crawler
pushd crawler
if not defined DB_HOST set DB_HOST=localhost
if not defined DB_PORT set DB_PORT=3306
if not defined DB_USER set DB_USER=novel
if not defined DB_PASSWORD set DB_PASSWORD=novel123
if not defined DB_NAME set DB_NAME=novel_rank
start "novel-crawler" /B "" cmd /c "set DB_HOST=%DB_HOST%&& set DB_PORT=%DB_PORT%&& set DB_USER=%DB_USER%&& set DB_PASSWORD=%DB_PASSWORD%&& set DB_NAME=%DB_NAME%&& python main.py" > "%~dp0..\logs\crawler.log" 2>&1
popd

REM --- frontend ---
:start_frontend
if /i "%TARGET%"=="frontend" goto :do_start_frontend
if /i "%TARGET%"=="all" goto :do_start_frontend
goto :start_done

:do_start_frontend
if not exist "frontend\node_modules" (
    echo [dev] installing frontend deps...
    pushd frontend
    call npm install || (popd & exit /b 1)
    popd
)
echo [dev] starting vite on :5173
pushd frontend
start "novel-frontend" /B "" cmd /c "npm.cmd run dev -- --host 0.0.0.0 --port 5173" > "%~dp0..\logs\frontend.log" 2>&1
popd

:start_done
echo.
echo [dev] services started. Logs: .\logs\
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8080/api
echo Swagger:   http://localhost:8080/doc.html
goto :eof

:do_stop
echo [dev] stopping: %TARGET%
for %%P in (backend crawler frontend) do (
    if /i not "%TARGET%"=="all" if /i not "%TARGET%"=="%%P" goto :skip_%%P
    if exist ".pids\%%P.pid" (
        set /p PID=<.pids\%%P.pid
        taskkill /F /T /PID !PID! 2>nul && echo [dev] stopped %%P pid !PID! || echo [dev] %%P not running
        del /Q .pids\%%P.pid 2>nul
    ) else (
        REM fallback: kill by window title
        taskkill /F /FI "WINDOWTITLE eq novel-%%P*" 2>nul >nul
        echo [dev] %%P: no pid file, killed by window title
    )
    goto :after_%%P
    :skip_%%P
)
:after_backend
:after_crawler
:after_frontend
goto :eof

:do_status
echo [dev] status:
for %%P in (backend crawler frontend) do (
    if exist ".pids\%%P.pid" (
        set /p PID=<.pids\%%P.pid
        tasklist /FI "PID eq !PID!" 2>nul | findstr /I "!PID!" >nul && (
            echo   [OK]   %%P pid !PID!
        ) || (
            echo   [--]   %%P
        )
    ) else (
        echo   [--]   %%P
    )
)
goto :eof

:do_logs
set "TARGET=%2"
if "%TARGET%"=="" set "TARGET=backend"
if not exist "logs\%TARGET%.log" (
    echo no log: logs\%TARGET%.log
    exit /b 1
)
powershell -Command "Get-Content -Path 'logs\%TARGET%.log' -Tail 50 -Wait"
goto :eof
