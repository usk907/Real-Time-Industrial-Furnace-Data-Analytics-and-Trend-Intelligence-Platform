@echo off
title IEIP - Android APK Build Pipeline
echo ======================================================================
echo    IEIP - Industrial Energy Intelligence Platform Mobile APK Builder
echo ======================================================================
echo.

:: Resolve project root directory (one level up from scripts)
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%\client"

:: 1. Ensure production web assets are built
echo [1/4] Compiling optimized React web application...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Web build failed. Aborting APK compilation.
    pause
    exit /b 1
)

:: 2. Initialize native Android project if not present
if not exist "android" (
    echo [2/4] Initializing native Android Capacitor shell...
    call npx cap add android
)

echo [2/4] Syncing web distribution into native Android project...
call npx cap sync android

:: 3. Detect Java & Android SDK
echo [3/4] Locating Java and Android SDK toolchains...

if "%JAVA_HOME%"=="" (
    if exist "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot" (
        set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
    ) else if exist "C:\Program Files\Java\jdk-17" (
        set "JAVA_HOME=C:\Program Files\Java\jdk-17"
    ) else if exist "C:\Program Files\Android\Android Studio\jbr" (
        set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
    )
)

if "%ANDROID_HOME%"=="" (
    if exist "%LOCALAPPDATA%\Android\Sdk" (
        set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
    )
)

if "%JAVA_HOME%" neq "" (
    set "PATH=%JAVA_HOME%\bin;%PATH%"
    echo Found Java: %JAVA_HOME%
)

if "%ANDROID_HOME%" neq "" (
    echo Found Android SDK: %ANDROID_HOME%
) else (
    echo [WARNING] ANDROID_HOME not set. If Gradle fails, make sure Android Studio SDK is installed.
)

:: 4. Build Debug APK via Gradle
echo [4/4] Compiling native Android APK via Gradle...
cd android
if exist "gradlew.bat" (
    call gradlew.bat assembleDebug
    if %ERRORLEVEL% equ 0 (
        if exist "app\build\outputs\apk\debug\app-debug.apk" (
            if not exist "%REPO_ROOT%\releases" mkdir "%REPO_ROOT%\releases"
            copy /y "app\build\outputs\apk\debug\app-debug.apk" "%REPO_ROOT%\releases\IEIP-Mobile.apk" >nul
            echo.
            echo ======================================================================
            echo  SUCCESS! Android APK built and saved to:
            echo  releases\IEIP-Mobile.apk
            echo ======================================================================
        )
    ) else (
        echo [ERROR] Gradle compilation encountered errors.
    )
) else (
    echo [ERROR] gradlew.bat not found inside android directory.
)

cd /d "%REPO_ROOT%"
pause
