@echo off
cd /d "C:\Users\Admin（无密码）\smart-kv-system"
echo === 1. Building ===
call npm run build
if not exist dist\index.html (echo BUILD FAILED && pause && exit /b 1)

echo === 2. Pushing source ===
"C:\Program Files\Git\bin\git.exe" add -A
"C:\Program Files\Git\bin\git.exe" commit -m "Auto deploy" 2>nul
"C:\Program Files\Git\bin\git.exe" push origin main 2>nul
echo Source push done

echo === 3. Deploying gh-pages (retry 5 times) ===
if exist "%TMP%\kv-site" rmdir /s /q "%TMP%\kv-site"
xcopy /E /Y dist\* "%TMP%\kv-site\" >nul
cd /d "%TMP%\kv-site"
"C:\Program Files\Git\bin\git.exe" init >nul
"C:\Program Files\Git\bin\git.exe" config user.email "d@k.local"
"C:\Program Files\Git\bin\git.exe" config user.name "Deploy"
"C:\Program Files\Git\bin\git.exe" add -A
"C:\Program Files\Git\bin\git.exe" commit -m "Deploy" >nul

for /l %%i in (1,1,5) do (
  echo Attempt %%i/5...
  "C:\Program Files\Git\bin\git.exe" push https://github.com/archie1996822-eng/smart-kv-system.git HEAD:gh-pages --force 2>&1 | findstr /C:"forced update" >nul && echo SUCCESS && goto :done
  timeout /t 5 >nul
)
echo FAILED after 5 attempts
:done
echo https://archie1996822-eng.github.io/smart-kv-system
pause
