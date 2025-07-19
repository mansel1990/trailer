Write-Host "Setting up Movie Trailer API..." -ForegroundColor Green

# Check if Python is available
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found at expected location" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "Setup complete! You can now run the server with:" -ForegroundColor Green
Write-Host "  .\run_server.bat" -ForegroundColor Cyan
Write-Host "  or" -ForegroundColor Cyan
Write-Host "  .\run_server.ps1" -ForegroundColor Cyan 