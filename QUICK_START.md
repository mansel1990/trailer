# Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Setup (First time only)
```powershell
.\setup.ps1
```

### 2. Start the Server
```powershell
# Option 1: Batch file
.\run_server.bat

# Option 2: PowerShell script
.\run_server.ps1

# Option 3: Direct command
py -m uvicorn main:app --reload
```

### 3. Test the API
```powershell
# Option 1: Batch file
.\test_api.bat

# Option 2: PowerShell script
.\test_api.ps1

# Option 3: Direct command
py test_local.py
```

## 🌐 API Endpoints

Once the server is running, visit:
- **API Status**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **Movies List**: http://localhost:8000/movies
- **Recent Popular Movies**: http://localhost:8000/movies/popular/recent
- **Upcoming Movies**: http://localhost:8000/movies/upcoming
- **API Docs**: http://localhost:8000/docs

## 🚀 Railway Deployment

1. **Push to Git**: Commit and push your changes
2. **Go to Railway**: [railway.app](https://railway.app)
3. **Connect Repository**: Create new project → Deploy from GitHub
4. **Set Environment Variables**:
   - `DB_HOST=turntable.proxy.rlwy.net`
   - `DB_PORT=25998`
   - `DB_USER=root`
   - `DB_PASSWORD=wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl`
   - `DB_NAME=trailer`
5. **Deploy**: Railway will automatically deploy your app

## ✅ Success Indicators

- Server starts without errors
- Test script shows all endpoints working
- API returns 40 Tamil movies
- Health endpoint returns "healthy"

## 🆘 Troubleshooting

**"uvicorn not found"**: Run `.\setup.ps1` to install dependencies

**"Batch file not recognized"**: Use `.\` prefix in PowerShell

**"Python not found"**: Use `py` command or full path to Python

**Database connection failed**: Check environment variables in Railway dashboard 