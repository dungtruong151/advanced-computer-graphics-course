@echo off
REM Compile LaTeX report to PDF
REM This script compiles the Assignment2_Report.tex file multiple times to resolve references

echo ========================================
echo Compiling Assignment 2 Report
echo ========================================
echo.

REM Check if pdflatex is available
where pdflatex >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pdflatex not found!
    echo Please install MiKTeX or TeX Live first.
    echo.
    echo Download from:
    echo - MiKTeX: https://miktex.org/download
    echo - TeX Live: https://www.tug.org/texlive/
    pause
    exit /b 1
)

echo Step 1: First compilation...
pdflatex -interaction=nonstopmode Assignment2_Report.tex
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: First compilation failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Second compilation (for references)...
pdflatex -interaction=nonstopmode Assignment2_Report.tex
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Second compilation failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Third compilation (for bibliography and cross-references)...
pdflatex -interaction=nonstopmode Assignment2_Report.tex
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Third compilation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Compilation successful!
echo ========================================
echo.
echo Output: Assignment2_Report.pdf
echo.

REM Clean up auxiliary files
echo Cleaning up auxiliary files...
del /Q *.aux *.log *.out *.toc 2>nul

echo.
echo Done! Opening PDF...
start Assignment2_Report.pdf

pause