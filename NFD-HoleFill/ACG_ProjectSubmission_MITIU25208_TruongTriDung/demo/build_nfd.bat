@echo off
echo === Setting up VS environment ===
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if errorlevel 1 (
    echo ERROR: vcvarsall.bat failed
    exit /b 1
)
echo === Building plugin ===
cd /d "C:\Users\ACE\Desktop\iu\Advanced Computer Graphics\meshlab-src\build2"
cmake --build . --target filter_nfd_holefill 2>&1
echo === Build exit code: %errorlevel% ===
