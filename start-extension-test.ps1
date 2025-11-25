# Quick Start Script for Extension Testing
# This script starts the backend server and provides helpful links

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AI Email Assistant - Extension Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "[OK] Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "[!] Virtual environment not detected" -ForegroundColor Yellow
    Write-Host "    Attempting to activate..." -ForegroundColor Yellow
    
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Virtual environment not found at .\venv\" -ForegroundColor Red
        Write-Host "        Please create it first: python -m venv venv" -ForegroundColor Red
        exit 1
    }
}

# Check if requirements are installed
Write-Host "`nChecking dependencies..." -ForegroundColor Cyan
$pipList = pip list 2>&1
if ($pipList -match "fastapi" -and $pipList -match "uvicorn") {
    Write-Host "[OK] Core dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[!] Dependencies may be missing" -ForegroundColor Yellow
    Write-Host "    Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check for .env file
if (Test-Path ".env") {
    Write-Host "[OK] .env file found" -ForegroundColor Green
    
    # Check for GEMINI_API_KEY
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "GEMINI_API_KEY=") {
        Write-Host "[OK] GEMINI_API_KEY configured" -ForegroundColor Green
    } else {
        Write-Host "[!] GEMINI_API_KEY not found in .env" -ForegroundColor Yellow
        Write-Host "    Add: GEMINI_API_KEY=your_key_here" -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] .env file not found" -ForegroundColor Yellow
    Write-Host "    Create .env with: GEMINI_API_KEY=your_key_here" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Starting Backend Server..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Backend will be available at:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000" -ForegroundColor White
Write-Host "`nUseful endpoints:" -ForegroundColor Yellow
Write-Host "  Health:    http://localhost:8000/health" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Extension: http://localhost:8000/api/extension/health" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Extension Setup (Do this in browser):" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. Open Chrome: chrome://extensions/" -ForegroundColor White
Write-Host "2. Enable Developer mode (top-right toggle)" -ForegroundColor White
Write-Host "3. Click 'Load unpacked'" -ForegroundColor White
Write-Host "4. Select folder: browser-extension\" -ForegroundColor White
Write-Host "5. Click extension icon → Settings" -ForegroundColor White
Write-Host "6. API Key: demo-key-001" -ForegroundColor Green
Write-Host "7. Tone: Professional" -ForegroundColor White
Write-Host "8. Click 'Save Settings'" -ForegroundColor White
Write-Host "9. Verify status: 'Connected' (green dot)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Test in Gmail:" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. Open: https://mail.google.com" -ForegroundColor White
Write-Host "2. Click 'Compose'" -ForegroundColor White
Write-Host "3. Look for: ✨ AI Draft button" -ForegroundColor White
Write-Host "4. Click button → See draft appear!" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Press CTRL+C to stop server" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Start the server
try {
    uvicorn src.api.main:app --reload --port 8000
} catch {
    Write-Host "`n[ERROR] Failed to start server: $_" -ForegroundColor Red
    Write-Host "Check the error above and try again." -ForegroundColor Red
    exit 1
}
