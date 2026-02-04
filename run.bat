@echo off
title Offer Flow Bot
cls
echo ===================================================
echo    Iniciando Sistema de Captura de Ofertas
echo ===================================================

:: 1. Ativa o ambiente virtual
call .venv\Scripts\activate

:: 2. Executa o script de limpeza (Mata processos do ChromeDriver)
python cleanup.py

:: 3. Executa o app principal
python app.py

echo.
echo ===================================================
echo    Execucao Finalizada.
echo ===================================================
pause