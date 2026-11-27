@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Video Scrap kurulumu
echo Bu betik gereken her seyi kendi kurar: .venv, paketler, ffmpeg.
echo Elle dosya kopyalaman veya baska program kurman gerekmez.
echo.

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto :kur
where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto :kur

echo Python bulunamadi. Otomatik kuruluyor (winget)...
where winget >nul 2>nul
if errorlevel 1 goto :python_yok
winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto :kur
where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto :kur
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set "PY=%%D\python.exe"
if defined PY goto :kur

:python_yok
echo.
echo HATA: Python kurulamadi.
echo 1) https://www.python.org/downloads/ adresini ac, Python'u indir.
echo 2) Kurulumun ilk ekraninda "Add python.exe to PATH" kutusunu isaretle.
echo 3) Bu pencereyi kapat, KUR.bat dosyasina tekrar cift tikla.
start "" https://www.python.org/downloads/
pause
exit /b 1

:kur
echo Python: %PY%
%PY% kur.py
if errorlevel 1 (
  echo.
  echo Kurulum tamamlanmadi. Yukaridaki son satirlari oku.
  pause
  exit /b 1
)
echo.
pause
exit /b 0
