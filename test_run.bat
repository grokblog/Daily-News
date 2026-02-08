@echo off
echo Starting Test Generation...
python blog_generator.py --test
if %errorlevel% neq 0 (
    echo.
    echo Generation Failed! Is Grok Gateway running on port 8017?
    echo Try running: ollama run mistral (or your model)
    pause
    exit /b %errorlevel%
)

echo.
echo Building Website...
python build_site.py

echo.
echo Starting Web Server...
python -m http.server 8000 --directory public
