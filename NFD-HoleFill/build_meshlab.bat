@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

set "SRCDIR=C:\Users\ACE\Desktop\iu\Advanced Computer Graphics\meshlab-src"
cd /d "%SRCDIR%"
if exist build2 rmdir /s /q build2
mkdir build2
cd build2

echo === Running CMake === > "%SRCDIR%\build_output.log" 2>&1
cmake "..\src" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="C:\Qt\5.15.2\msvc2019_64" -DCMAKE_C_COMPILER=cl -DCMAKE_CXX_COMPILER=cl -Wno-dev >> "%SRCDIR%\build_output.log" 2>&1
if %ERRORLEVEL% neq 0 (
    echo CMAKE FAILED >> "%SRCDIR%\build_output.log"
    exit /b 1
)

echo === CMAKE OK. Building... === >> "%SRCDIR%\build_output.log" 2>&1
ninja -j%NUMBER_OF_PROCESSORS% >> "%SRCDIR%\build_output.log" 2>&1
echo === BUILD DONE exit=%ERRORLEVEL% === >> "%SRCDIR%\build_output.log" 2>&1
