@echo off
chcp 65001 > nul

echo ==================================
echo   MinerU Test
echo ==================================
echo.

echo Checking server...
curl -s http://localhost:8000/ > nul 2>&1
if errorlevel 1 (
    echo ERROR - Server not running!
    echo.
    echo Start server:
    echo   cd backend
    echo   run_server.bat
    pause
    exit /b 1
)

echo OK - Server is running
echo.

echo Enter PDF filename in /docu folder:
set /p filename=Filename:

echo.
echo Parsing: %filename%
echo Please wait...
echo.

curl -X POST "http://localhost:8000/parse" ^
  -H "Content-Type: application/json" ^
  -d "{\"filename\": \"%filename%\", \"options\": {\"parsing_method\": \"mineru\", \"save_to_output_folder\": true}}"

echo.
echo.
echo Done! Check /output folder for results.
echo.
pause
