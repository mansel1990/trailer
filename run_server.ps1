Write-Host "Starting Movie Trailer API Server..." -ForegroundColor Green
C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 