@echo off
chcp 65001 > nul
echo ======================================================
echo  OTALOGIA - DISPARAR PUBLICACAO DO INSTAGRAM
echo ======================================================
cd /d "%~dp0"
python "%~dp0..\instagram_publisher.py" --auto-next
pause
