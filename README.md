# Movie Trailer API

A FastAPI-based REST API for movie data and recommendations, deployed on Railway.

## Features

- Movie data retrieval
- Tamil movie recommendations
- Health check endpoints
- CORS enabled for frontend integration

## API Endpoints

- `GET /` - Root endpoint with API status
- `GET /health` - Health check endpoint
- `GET /movies` - Get list of Tamil movies (limited to 40, ordered by popularity)
- `GET /movies/{movie_id}` - Get specific movie details

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (create a `.env` file):
```env
DB_HOST=your_db_host
DB_PORT=your_db_port
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

3. Run the application:
```bash
# Option 1: Using the batch file (Windows PowerShell)
.\run_server.bat

# Option 2: Using PowerShell script
.\run_server.ps1

# Option 3: Using Python directly
py -m uvicorn main:app --reload
```

## Railway Deployment

This project is configured for Railway deployment with the following files:

- `main.py` - Main FastAPI application
- `requirements.txt` - Python dependencies
- `Procfile` - Railway process configuration
- `runtime.txt` - Python version specification

### Environment Variables for Railway

Set these in your Railway project dashboard:

- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name

## Project Structure

```
trailer/
├── main.py                 # Main FastAPI application
├── requirements.txt        # Python dependencies
├── Procfile              # Railway process configuration
├── runtime.txt           # Python version
├── README.md            # This file
└── pythonProject1/      # Original project files
    ├── data_collection/  # Data collection scripts
    ├── pipeline/         # ML pipeline scripts
    ├── util/            # Utility functions
    └── config_sql.py    # Database configuration
```

## Testing

Test the API locally:

```bash
# Option 1: Using the batch file (Windows PowerShell)
.\test_api.bat

# Option 2: Using PowerShell script
.\test_api.ps1

# Option 3: Using Python directly
py test_local.py
```

## Database

The application connects to a MySQL database containing movie information. The main query retrieves Tamil movies ordered by popularity.