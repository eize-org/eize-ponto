@echo off
echo ================================
echo      Atualizando pOnto
echo ================================

:: ---- BACKUP ----
echo.
echo Criando backup antes de atualizar...

for /f "tokens=1-6 delims=/:. " %%a in ("%date% %time%") do (
    set DIA=%%a
    set MES=%%b
    set ANO=%%c
    set HOR=%%d
    set MIN=%%e
    set SEG=%%f
)
set PASTA_BACKUP=backup\%ANO%-%MES%-%DIA%_%HOR%-%MIN%-%SEG%
mkdir "%PASTA_BACKUP%" 2>nul

set BACKUP_OK=1

if exist db.sqlite3 (
    copy /Y db.sqlite3 "%PASTA_BACKUP%\db.sqlite3" >nul
    echo   [OK] Banco de dados copiado.
) else (
    echo   [AVISO] db.sqlite3 nao encontrado, pulando.
)

if exist .env (
    copy /Y .env "%PASTA_BACKUP%\.env" >nul
    echo   [OK] Arquivo .env copiado.
) else (
    echo   [AVISO] .env nao encontrado, pulando.
)

echo   Backup salvo em: %PASTA_BACKUP%
echo.
:: ---- FIM DO BACKUP ----

echo Baixando atualizacoes do GitHub...
git pull origin main

echo.
echo Instalando dependencias...
.venv\Scripts\pip install -r requirements.txt --quiet

echo.
echo Rodando migracoes...
.venv\Scripts\python manage.py makemigrations
.venv\Scripts\python manage.py migrate

echo.
echo Gerando tokens pendentes (se houver)...
.venv\Scripts\python manage.py shell -c "from core.models import Bolsista; [b.save() for b in Bolsista.objects.filter(token='')]"

echo.
echo Aplicando migracoes finais...
.venv\Scripts\python manage.py makemigrations
.venv\Scripts\python manage.py migrate

echo.
echo ================================
echo  Atualizacao concluida!
echo  Execute o iniciar.bat para usar
echo ================================
pause