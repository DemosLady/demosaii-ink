@echo off
chcp 65001 >nul

echo ========================================
echo   demosaii ink - Fetch Etsy Listings
echo ========================================
echo.

cd /d D:\AI\CODE\learning-curve-auto\sites\demosaii-ink

echo Installing dependencies...
pip install requests python-dotenv --quiet --break-system-packages 2>nul || pip install requests python-dotenv --quiet

echo.
python fetch_etsy.py

echo.
pause
