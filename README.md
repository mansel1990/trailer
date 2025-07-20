# Movie Trailer API

A FastAPI-based REST API for movie recommendations and data management.

## Project Structure

```
├── main.py              # Main FastAPI application
├── models.py            # Pydantic models for data validation
├── database.py          # Database configuration and utilities
├── services.py          # Business logic and background tasks
├── test_api.py          # Simple API testing script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Movie Data Management**: Retrieve and filter movie data
- **User Rating System**: Async processing for user ratings
- **Watchlist Management**: Add/remove movies from user watchlists
- **Personalized Recommendations**: ML-based movie recommendations
- **Multi-language Support**: Tamil, Telugu, Kannada, Hindi, Malayalam, Bengali

## API Endpoints

### Basic Endpoints
- `GET /` - Root endpoint with API status
- `GET /health` - Health check endpoint

### Movie Endpoints
- `GET /movies` - Get list of Tamil movies (limited to 40, ordered by popularity)
- `GET /movies/popular/recent` - Get movies from last 2 weeks sorted by popularity score
- `GET /movies/upcoming` - Get movies releasing in next 2 weeks

### Rating Endpoints
- `POST /ratings` - Add or update user rating for a movie (async processing)
- `GET /ratings/{clerk_user_id}` - Get all ratings for a specific user

### Watchlist Endpoints
- `POST /watchlist` - Add movie to user's watchlist (async processing)
- `GET /watchlist/{clerk_user_id}` - Get all movies in user's watchlist
- `DELETE /remove-from-watchlist` - Remove movie from user's watchlist (async processing)

### Recommendation Endpoints
- `GET /recommendations/{clerk_user_id}` - Get movie recommendations based on predicted scores

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