@echo off
REM =============================================================================
REM start.bat - Deploy the full stack with Docker Compose
REM =============================================================================
REM Usage:
REM   start.bat                  REM docker compose up -d
REM   start.bat --build          REM build first, then up
REM   start.bat --no-cache       REM build with no cache, then up
REM   start.bat [service...]     REM up only specific service(s)
REM =============================================================================
cd /d "%~dp0\.."

where docker >nul 2>nul
if errorlevel 1 (
    echo Error: docker not found. Install Docker first.
    exit /b 1
)
docker compose version >nul 2>nul
if errorlevel 1 (
    echo Error: docker compose v2 not installed.
    exit /b 1
)
if not exist .env (
    echo [start] .env not found. Copying from .env.example
    copy /Y .env.example .env >nul
)

REM --- build if requested ---
set "BUILD_FIRST=0"
for %%A in (%*) do (
    if "%%A"=="--build"   set "BUILD_FIRST=1"
    if "%%A"=="--rebuild" set "BUILD_FIRST=1"
    if "%%A"=="--no-cache" set "BUILD_FIRST=1"
)
if "%BUILD_FIRST%"=="1" (
    echo [start] building images first...
    docker compose build %*
    if errorlevel 1 exit /b 1
)

REM --- up ---
echo [start] starting services...
docker compose up -d %*
if errorlevel 1 exit /b 1

echo.
echo [start] waiting for MySQL healthcheck (up to 60s)...
set "ROOT_PWD="
for /f "tokens=1,* delims==" %%K in ('findstr /B "MYSQL_ROOT_PASSWORD=" .env') do set "ROOT_PWD=%%L"

set /a TRIED=0
:wait_mysql
set /a TRIED+=1
if !TRIED! GTR 30 goto :mysql_done
docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -p%ROOT_PWD% --silent >nul 2>nul
if not errorlevel 1 (
    echo [start] MySQL ready.
    goto :mysql_done
)
timeout /t 2 /nobreak >nul
goto :wait_mysql
:mysql_done

echo.
echo ==========================================
echo   Services started!
echo ==========================================
echo   Frontend:   http://localhost
echo   Backend:    http://localhost:8080/api
echo   Swagger:    http://localhost:8080/doc.html
echo   Login:      admin / admin123
echo ==========================================
echo   Stop:       scripts\stop.bat
echo   Rebuild:    scripts\build.bat --no-cache ^&^& scripts\start.bat
echo ==========================================
