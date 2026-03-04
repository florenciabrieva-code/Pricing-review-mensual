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

:: Detectar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado en el PATH
    exit /b 1
)

:: Instalar dependencias si hace falta
echo [1/4] Verificando dependencias...
pip install -q -r scripts\requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Fallo la instalacion de dependencias
    exit /b 1
)

:: Correr el reporte
echo [2/4] Generando reporte en BigQuery...
python scripts\run_report.py --year %YEAR% --month %MONTH%
if %errorlevel% neq 0 (
    echo ERROR: Fallo la generacion del reporte
    exit /b 1
)

:: Actualizar index
echo [3/4] Actualizando index.html...
python scripts\update_index.py
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
