@echo off
echo Checking System Status...
echo.

echo 1. Checking if python is installed...
python --version

echo.
echo 2. Checking if Port 8017 is interacting...
netstat -an | find "8017"

echo.
echo 3. Testing connection to Grok API Gateway...
curl -v http://localhost:8017/health

echo.
echo If Step 2 returns nothing, main.py is NOT running.
echo If Step 3 fails, there is a connection issue.
pause
