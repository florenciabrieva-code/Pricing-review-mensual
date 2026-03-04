@echo off
:: ============================================================
:: Generador de Monthly Review
:: Uso: generar_reporte.bat <year> <month>
:: Ejemplo: generar_reporte.bat 2026 3
:: ============================================================

set YEAR=%1
set MONTH=%2

if "%YEAR%"=="" (
    echo ERROR: Falta el anio. Uso: generar_reporte.bat ^<year^> ^<month^>
    echo Ejemplo: generar_reporte.bat 2026 3
    exit /b 1
)
if "%MONTH%"=="" (
    echo ERROR: Falta el mes. Uso: generar_reporte.bat ^<year^> ^<month^>
    echo Ejemplo: generar_reporte.bat 2026 3
    exit /b 1
)

echo.
echo ============================================================
echo  Monthly Review - %YEAR%-%MONTH%
echo ============================================================
echo.

:: Detectar uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv no encontrado. Instalar desde https://docs.astral.sh/uv/
    exit /b 1
)

:: Correr el reporte
echo [2/4] Generando reporte en BigQuery...
uv run --with-requirements scripts\requirements.txt scripts\run_report.py --year %YEAR% --month %MONTH%
if %errorlevel% neq 0 (
    echo ERROR: Fallo la generacion del reporte
    exit /b 1
)

:: Actualizar index
echo [3/4] Actualizando index.html...
uv run --with-requirements scripts\requirements.txt scripts\update_index.py
if %errorlevel% neq 0 (
    echo ERROR: Fallo la actualizacion del index
    exit /b 1
)

:: Commit y push
echo [4/4] Publicando en GitHub...
git add reports\ index.html
git diff --staged --quiet && (
    echo Sin cambios nuevos, nada para commitear.
) || (
    git commit -m "report: reporte %YEAR%-%MONTH%"
    git push
    echo.
    echo Reporte publicado correctamente.
    echo URL: https://florenciabrieva-code.github.io/Pricing-review-mensual/reports/%YEAR%-%MONTH%/
)

echo.
echo Listo!
