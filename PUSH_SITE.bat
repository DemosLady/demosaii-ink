@echo off
chcp 65001 >nul

echo ========================================
echo   demosaii ink - Push to GitHub Pages
echo ========================================
echo.

set REPO_NAME=demosaii-ink
set REPO_URL=https://github.com/DemosLady/%REPO_NAME%.git
set SITE_FOLDER=D:\AI\CODE\learning-curve-auto\sites\demosaii-ink

:: Check if folder exists
if not exist "%SITE_FOLDER%" (
    echo [SETUP] Creating project folder...
    mkdir "%SITE_FOLDER%"
)

cd /d "%SITE_FOLDER%"

:: Check if git is initialized
if not exist ".git" (
    echo [SETUP] Initializing git repo...
    git init
    git remote add origin %REPO_URL%
    git branch -M main
    echo.
    echo ----------------------------------------
    echo   FIRST TIME? Create the repo on GitHub:
    echo   https://github.com/new
    echo   Name: %REPO_NAME%
    echo   Public repo, no README
    echo   Then run this BAT again.
    echo ----------------------------------------
    echo.
)

:: Copy the HTML file as index.html if not already there
if not exist "index.html" (
    echo [INFO] No index.html found in %SITE_FOLDER%
    echo [INFO] Copy your demosaii-ink-v2.html here and rename it to index.html
    echo.
    pause
    exit /b
)

:: Git add, commit, push
echo [GIT] Adding files...
git add -A

echo.
set /p COMMIT_MSG=Enter commit message (or press Enter for default): 
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update demosaii ink site

echo [GIT] Committing: %COMMIT_MSG%
git commit -m "%COMMIT_MSG%"

echo [GIT] Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo   DONE! Your site will be live at:
echo   https://demoslady.github.io/%REPO_NAME%/
echo.
echo   If this is your first push, enable
echo   GitHub Pages in repo Settings:
echo   Settings ^> Pages ^> Source: main ^> Save
echo ========================================
echo.
pause
