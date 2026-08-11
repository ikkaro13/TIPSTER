@echo off
title Tipster AI Quad-Core Launcher
color 0B

echo ========================================================
echo          INICIANDO TIPSTER AI (MODO LOCAL)
echo ========================================================
echo.
echo [1/2] Encendiendo Motor de Inteligencia Artificial (Backend)...
start "Tipster AI Backend" cmd /k "d: & cd \Work\ANTIGRAVITY\TIPSTER\backend & python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/2] Encendiendo Interfaz Grafica (Frontend)...
start "Tipster AI Frontend" cmd /k "d: & cd \Work\ANTIGRAVITY\TIPSTER\frontend & npm run dev -- -H 0.0.0.0"

echo.
echo ========================================================
echo   TODO LISTO! LAS 2 CONSOLAS SE ABRIERON AUTOMATICAMENTE
echo ========================================================
echo.
echo Para abrir en tu PC:      http://localhost:3000
echo Para abrir en tu celular: http://192.168.1.14:3000
echo.
echo NOTA: Deja las dos consolas negras nuevas abiertas mientras usas la app.
echo.
pause
