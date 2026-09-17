@echo off
echo ========================================
echo   Sincronizando Historico com GitHub
echo ========================================
echo.
.venv\Scripts\python manage.py sincronizar_tudo
echo.
pause
