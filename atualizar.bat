@echo off
echo ================================
echo      Atualizando pOnto
echo ================================

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