@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem Video Scrap - tek baslatici.
rem Cift tikla: arayuz konsol penceresi olmadan acilir.
rem Hata olursa uygulama mesaj kutusu gosterir.

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" video_scrap.py
  exit /b 0
)
if exist ".venv\Scripts\python.exe" (
  start "" ".venv\Scripts\python.exe" video_scrap.py
  exit /b 0
)
where pythonw.exe >nul 2>&1
if not errorlevel 1 (
  start "" pythonw.exe video_scrap.py
  exit /b 0
)
where python.exe >nul 2>&1
if not errorlevel 1 (
  python video_scrap.py
  if errorlevel 1 pause
  exit /b 0
)

echo Python bulunamadi.
echo Once KUR.bat dosyasini calistir.
pause
exit /b 1
