@echo off
echo ==========================================
echo   INICIANDO TESTE INTUITIVE CARE (ERIK)
echo ==========================================

:: 1. Entra na pasta do Backend e inicia a API
echo Iniciando API (Flask)...
start "Backend - API" cmd /k "cd backend-intuitive && python api.py"

:: 2. Entra na pasta do Frontend e inicia o Vue.js
echo Iniciando Frontend (Vue.js)...
start "Frontend - Vue" cmd /k "cd frontend-intuitive && npm run dev"

:: 3. Aguarda o carregamento e abre o navegador
timeout /t 5
start http://localhost:5173

echo.
echo Tudo rodando! Verifique as duas janelas abertas.
pause