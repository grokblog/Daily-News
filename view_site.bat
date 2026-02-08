@echo off
echo ===========================================
echo  Grok Blog Generator - View Results
echo ===========================================

echo.
echo 1. Building Site...
python build_site.py

echo.
echo 2. Opening in Browser...
echo Server running at http://localhost:8000
start http://localhost:8000

echo.
echo 3. Starting Local Server...
cd public
python -m http.server 8000
