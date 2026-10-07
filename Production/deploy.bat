@echo off
echo === Деплой dev -^> Production ===
cd /d D:\Newgame\EchoSmyta\Production

echo [1/3] Копирую бэк (без .env и мусора)...
robocopy ..\services .\services /E /XD .venv node_modules __pycache__ .git .pytest_cache /XF .env /NFL /NDL /NJH /NJS /NC /NS

echo [2/3] Копирую фронт (без .env и мусора)...
robocopy ..\frontend .\frontend\echo-smyta /E /XD node_modules dist .git /XF .env /NFL /NDL /NJH /NJS /NC /NS

echo [3/3] Пересобираю и поднимаю контейнеры...
docker compose up -d --build

echo === Готово! Открывай http://localhost ===
pause