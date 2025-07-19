# Railway Deployment Guide

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)
3. **Database**: You'll need a MySQL database (Railway provides this)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Your project is now ready for Railway deployment with these files:
- ✅ `main.py` - Main FastAPI application
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Railway process configuration
- ✅ `runtime.txt` - Python version
- ✅ `.gitignore` - Excludes unnecessary files

### 2. Deploy to Railway

1. **Connect Repository**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Add Database** (if needed):
   - In your Railway project dashboard
   - Click "New" → "Database" → "MySQL"
   - Railway will provide connection details

3. **Set Environment Variables**:
   - In your Railway project dashboard
   - Go to "Variables" tab
   - Add these environment variables:
   ```
   DB_HOST=your_database_host
   DB_PORT=your_database_port
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_NAME=your_database_name
   ```

4. **Deploy**:
   - Railway will automatically detect your Python app
   - It will install dependencies from `requirements.txt`
   - The app will start using the `Procfile`

### 3. Verify Deployment

1. **Check Logs**:
   - In Railway dashboard, go to "Deployments"
   - Click on the latest deployment
   - Check logs for any errors

2. **Test Endpoints**:
   - Your app will be available at: `https://your-app-name.railway.app`
   - Test these endpoints:
     - `GET /` - Should return API status
     - `GET /health` - Should return health status
     - `GET /movies` - Should return movie data

### 4. Custom Domain (Optional)

1. In Railway dashboard, go to "Settings"
2. Click "Custom Domains"
3. Add your domain and configure DNS

## Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
export DB_HOST=your_host
export DB_PORT=your_port
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_NAME=your_database

# Run the application
uvicorn main:app --reload

# Test the API
python test_local.py
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check environment variables in Railway dashboard
   - Verify database credentials
   - Ensure database is accessible from Railway

2. **Build Failed**:
   - Check `requirements.txt` for correct dependencies
   - Verify Python version in `runtime.txt`
   - Check Railway logs for specific errors

3. **App Not Starting**:
   - Verify `Procfile` syntax
   - Check if port is correctly set to `$PORT`
   - Review application logs

### Useful Commands

```bash
# Check Railway CLI (if installed)
railway login
railway status
railway logs

# Local development
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | `turntable.proxy.rlwy.net` |
| `DB_PORT` | Database port | `25998` |
| `DB_USER` | Database username | `root` |
| `DB_PASSWORD` | Database password | `wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl` |
| `DB_NAME` | Database name | `trailer` |
| `PORT` | Application port | `8000` (set by Railway) |

## API Documentation

Once deployed, your API documentation will be available at:
- Swagger UI: `https://your-app-name.railway.app/docs`
- ReDoc: `https://your-app-name.railway.app/redoc` 