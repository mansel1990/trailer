from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import asyncio
import os
import logging, sys
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger()
import sys

# Import our modules
from models import (
    Movie, MovieWithStats, UserRatingRequest, UserRatingResponse,
    WatchlistRequest, WatchlistResponse, MovieRecommendation, UserSummary, LoginRequest,
    SemanticSearchRequest, SemanticMovieResult
)
from database import execute_query, execute_update
from services import (
    update_user_rating_async, add_to_watchlist_async, remove_from_watchlist_async
)

# Add imports for embeddings
import numpy as np
from sentence_transformers import SentenceTransformer
import json

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Movie Trailer API",
    description="""
    # Movie Trailer API 🎬
    
    A comprehensive REST API for movie recommendations, ratings, and watchlist management.
    
    ## Features
    - **Movie Discovery**: Browse movies by popularity, recent releases, and upcoming titles
    - **Personalized Recommendations**: Get AI-powered movie recommendations based on user preferences
    - **User Ratings**: Rate movies and track your ratings history
    - **Watchlist Management**: Add/remove movies from your personal watchlist
    - **Multi-language Support**: Tamil, Telugu, Kannada, Hindi, Malayalam, Bengali
    
    ## Quick Start
    1. **Health Check**: `GET /health` - Verify API status
    2. **Browse Movies**: `GET /movies` - Get popular Tamil movies
    3. **Get Recommendations**: `GET /recommendations/{clerk_user_id}` - Personalized recommendations
    4. **Rate Movies**: `POST /ratings` - Rate a movie (0-5 stars)
    5. **Manage Watchlist**: `POST /watchlist` - Add movie to watchlist
    
    ## Authentication
    This API uses Clerk user IDs for user identification. Pass your Clerk user ID in the URL path.
    """,
    version="1.0.0",
    contact={
        "name": "Movie Trailer API Support",
        "email": "support@movietrailer.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# BASIC ENDPOINTS
# ============================================================================

@app.get("/", tags=["Basic"])
def read_root():
    """
    # Root Endpoint
    
    Returns basic API information and status.
    
    **Response:**
    - `message`: API status message
    """
    return {"message": "Movie Trailer API is running!"}

@app.get("/health", tags=["Basic"])
def health_check():
    """
    # Health Check
    
    Verify that the API is running and healthy.
    
    **Response:**
    - `status`: Health status ("healthy" if API is working)
    
    **Use Cases:**
    - Monitor API availability
    - Load balancer health checks
    - Deployment verification
    """
    return {"status": "healthy"}

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/add_user", response_model=dict, tags=["Authentication"])
async def add_user(login_request: LoginRequest):
    """
    # Add User
    
    Register a new user or update existing user information. This endpoint checks if an email already exists
    and throws an error if it does, otherwise inserts the user into the database.
    
    **Features:**
    - Email uniqueness validation
    - Automatic user registration
    - Clerk user ID integration
    - Error handling for duplicate emails
    
    **Request Body:**
    ```json
    {
      "clerkUserId": "user_2abc123def456",
      "email": "user@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "imageUrl": "https://example.com/image.jpg",
      "username": "johndoe"
    }
    ```
    
    **Parameters:**
    - `clerkUserId` (string, required): Clerk user ID
    - `email` (string, optional): User's email address
    - `firstName` (string, optional): User's first name
    - `lastName` (string, optional): User's last name
    - `imageUrl` (string, optional): User's profile image URL
    - `username` (string, optional): User's chosen username
    
    **Response:**
    ```json
    {
      "message": "User registered successfully",
      "clerk_user_id": "user_2abc123def456",
      "username": "johndoe",
      "status": "success"
    }
    ```
    
    **Error Responses:**
    - `400 Bad Request`: Username already exists
    - `500 Internal Server Error`: Database or processing error
    
    **Use Cases:**
    - User registration
    - Email validation
    - Clerk integration
    - User profile updates
    """
    try:
        # Check if email already exists (if email is provided)
        if login_request.email:
            email_check_query = """
                SELECT clerk_user_id FROM users WHERE email = %s
            """
            existing_user = execute_query(email_check_query, (login_request.email,))
            
            if existing_user:
                # Check if the existing user is the same as the current user
                existing_clerk_id = existing_user[0]['clerk_user_id']
                if existing_clerk_id != login_request.clerkUserId:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Email '{login_request.email}' already exists"
                    )
        
        # Check if user already exists by clerk_user_id
        user_check_query = """
            SELECT clerk_user_id FROM users WHERE clerk_user_id = %s
        """
        existing_user = execute_query(user_check_query, (login_request.clerkUserId,))
        
        if existing_user:
            # User already exists, update their information
            update_query = """
                UPDATE users 
                SET email = %s, first_name = %s, last_name = %s, image_url = %s, username = %s
                WHERE clerk_user_id = %s
            """
            
            execute_update(update_query, (
                login_request.email,
                login_request.firstName,
                login_request.lastName,
                login_request.imageUrl,
                login_request.username,
                login_request.clerkUserId
            ))
            
            return {
                "message": "User information updated",
                "clerk_user_id": login_request.clerkUserId,
                "username": login_request.username,
                "status": "updated"
            }
        
        # Insert new user
        insert_query = """
            INSERT INTO users (clerk_user_id, email, first_name, last_name, image_url, username)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        execute_update(insert_query, (
            login_request.clerkUserId,
            login_request.email,
            login_request.firstName,
            login_request.lastName,
            login_request.imageUrl,
            login_request.username
        ))
        
        return {
            "message": "User registered successfully",
            "clerk_user_id": login_request.clerkUserId,
            "username": login_request.username,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

# ============================================================================
# MOVIE ENDPOINTS
# ============================================================================

@app.get("/movies", response_model=List[MovieWithStats], tags=["Movies"])
def get_movies(clerk_user_id: Optional[str] = Query(None, description="Clerk user ID for user-specific info")):
    """
    # Get Popular Tamil Movies
    Retrieve a list of popular Tamil movies, ordered by popularity.
    If clerk_user_id is provided, includes watched, user_rating, and is_watchlisted fields if present.
    """
    try:
        if clerk_user_id:
            query = """
                SELECT m.id, m.title, m.overview, m.poster_path,
                       COALESCE(m.popularity, 0) as popularity,
                       COALESCE(m.vote_count, 0) as vote_count,
                       COALESCE(m.vote_average, 0) as vote_average,
                       DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                       (COALESCE(m.popularity, 0) + COALESCE(m.vote_count, 0) + COALESCE(m.vote_average, 0)) as popularity_score,
                       ur.rating as user_rating,
                       CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                       CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM movies m
                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                WHERE m.original_language='ta' AND m.release_date<CURRENT_TIMESTAMP()
                ORDER BY m.popularity DESC 
                LIMIT 40
            """
            rows = execute_query(query, (clerk_user_id, clerk_user_id))
        else:
            query = """
                SELECT id, title, overview, poster_path, popularity, vote_count, vote_average, DATE_FORMAT(release_date, '%Y-%m-%d') as release_date, (COALESCE(popularity, 0) + COALESCE(vote_count, 0) + COALESCE(vote_average, 0)) as popularity_score
                FROM movies 
                WHERE original_language='ta' AND release_date<CURRENT_TIMESTAMP()
                ORDER BY popularity DESC 
                LIMIT 40
            """
            rows = execute_query(query)
        for row in rows:
            row["watched"] = bool(row.get("watched", 0))
            row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return rows
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/movies/popular/recent", response_model=List[MovieWithStats], tags=["Movies"])
def get_recent_popular_movies(clerk_user_id: Optional[str] = Query(None, description="Clerk user ID for user-specific info")):
    """
    # Get Recent Popular Movies
    Retrieve movies from the last 3 weeks sorted by popularity score.
    If clerk_user_id is provided, includes watched, user_rating, and is_watchlisted fields if present.
    """
    try:
        if clerk_user_id:
            query = """
                SELECT m.id, m.title, m.overview, m.poster_path,
                       COALESCE(m.popularity, 0) as popularity,
                       COALESCE(m.vote_count, 0) as vote_count,
                       COALESCE(m.vote_average, 0) as vote_average,
                       DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                       (COALESCE(m.popularity, 0) + COALESCE(m.vote_count, 0) + COALESCE(m.vote_average, 0)) as popularity_score,
                       ur.rating as user_rating,
                       CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                       CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM movies m
                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                WHERE m.release_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 WEEK)
                  AND m.release_date <= CURRENT_DATE()
                ORDER BY m.release_date desc, m.popularity DESC
                LIMIT 40
            """
            rows = execute_query(query, (clerk_user_id, clerk_user_id))
        else:
            query = """
                SELECT id, title, overview, poster_path, popularity, vote_count, vote_average, DATE_FORMAT(release_date, '%Y-%m-%d') as release_date, (COALESCE(popularity, 0) + COALESCE(vote_count, 0) + COALESCE(vote_average, 0)) as popularity_score
                FROM movies 
                WHERE release_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 WEEK)
                  AND release_date <= CURRENT_DATE()
                ORDER BY release_date desc, popularity DESC
                LIMIT 40
            """
            rows = execute_query(query)
        for row in rows:
            row["watched"] = bool(row.get("watched", 0))
            row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return rows
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/movies/upcoming", response_model=List[MovieWithStats], tags=["Movies"])
def get_upcoming_movies(clerk_user_id: Optional[str] = Query(None, description="Clerk user ID for user-specific info")):
    """
    # Get Upcoming Movies
    Retrieve movies that are going to be released in the next 4 weeks.
    If clerk_user_id is provided, includes watched, user_rating, and is_watchlisted fields if present.
    """
    try:
        if clerk_user_id:
            query = """
                SELECT m.id, m.title, m.overview, m.poster_path,
                       COALESCE(m.popularity, 0) as popularity,
                       COALESCE(m.vote_count, 0) as vote_count,
                       COALESCE(m.vote_average, 0) as vote_average,
                       DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                       (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                       ur.rating as user_rating,
                       CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                       CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM movies m
                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                WHERE m.release_date > CURRENT_DATE()
                  AND m.release_date <= DATE_ADD(CURRENT_DATE(), INTERVAL 4 WEEK)
                  AND m.original_language IN ('ta', 'te', 'kn', 'hi', 'ml', 'bn')
                ORDER BY m.release_date ASC, popularity_score DESC
                LIMIT 40
            """
            rows = execute_query(query, (clerk_user_id, clerk_user_id))
        else:
            query = """
                SELECT id, title, overview, poster_path, popularity, vote_count, vote_average, DATE_FORMAT(release_date, '%Y-%m-%d') as release_date, (COALESCE(popularity, 0) * COALESCE(vote_count, 0) * COALESCE(vote_average, 0)) as popularity_score
                FROM movies 
                WHERE release_date > CURRENT_DATE()
                  AND release_date <= DATE_ADD(CURRENT_DATE(), INTERVAL 4 WEEK)
                  AND original_language IN ('ta', 'te', 'kn', 'hi', 'ml', 'bn')
                ORDER BY release_date ASC, popularity_score DESC
                LIMIT 40
            """
            rows = execute_query(query)
        for row in rows:
            row["watched"] = bool(row.get("watched", 0))
            row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return rows
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/search", response_model=List[MovieRecommendation], tags=["Movies"])
def search_movies(
    q: str = Query(..., description="Search term for movie title"),
    clerk_user_id: Optional[str] = Query(None, description="Clerk user ID for watched/user_rating info")
):
    """
    # Search Movies by Title
    Returns movies whose title contains the search term (case-insensitive substring match), ordered by popularity.
    If clerk_user_id is provided, includes watched, user_rating, and is_watchlisted fields if present.
    """
    try:
        if clerk_user_id:
            query = """
                SELECT m.id, m.title, m.overview, m.poster_path,
                       DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                       m.original_language,
                       COALESCE(m.popularity, 0) as popularity,
                       COALESCE(m.vote_count, 0) as vote_count,
                       COALESCE(m.vote_average, 0) as vote_average,
                       COALESCE(r.predicted_rating, 0) as predicted_rating,
                       ur.rating as user_rating,
                       CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                       CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted,
                       CASE WHEN ur.rating IS NOT NULL THEN SQRT(COALESCE(r.predicted_rating, 0) * 5 * ur.rating)
                            ELSE (COALESCE(r.predicted_rating, 0) * 5)
                       END as predicted_star_rating
                FROM movies m
                LEFT JOIN recommendations r ON m.id = r.movie_id AND r.user_id = %s
                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                WHERE LOWER(m.title) LIKE %s
                ORDER BY m.popularity DESC
                LIMIT 60
            """
            search_pattern = f"%{q.lower()}%"
            rows = execute_query(query, (clerk_user_id, clerk_user_id, clerk_user_id, search_pattern))
        else:
            query = """
                SELECT id, title, overview, poster_path, 
                       DATE_FORMAT(release_date, '%Y-%m-%d') as release_date,
                       original_language, 
                       COALESCE(popularity, 0) as popularity, 
                       COALESCE(vote_count, 0) as vote_count, 
                       COALESCE(vote_average, 0) as vote_average
                FROM movies 
                WHERE LOWER(title) LIKE %s
                ORDER BY popularity DESC
                LIMIT 60
            """
            search_pattern = f"%{q.lower()}%"
            rows = execute_query(query, (search_pattern,))
        results = []
        for row in rows:
            if clerk_user_id:
                row["predicted_rating"] = row.get("predicted_rating", 0.0)
                row["predicted_star_rating"] = row.get("predicted_star_rating", 0.0)
                row["user_rating"] = row.get("user_rating")
                row["watched"] = bool(row.get("watched", 0))
                row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
            else:
                row["predicted_rating"] = 0.0
                row["predicted_star_rating"] = 0.0
                row["user_rating"] = None
                row["watched"] = False
                row["is_watchlisted"] = False
            results.append(row)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ============================================================================
# RATING ENDPOINTS
# ============================================================================

@app.post("/ratings", response_model=dict, tags=["Ratings"])
async def add_user_rating(rating_request: UserRatingRequest):
    """
    # Add or Update User Rating
    
    Rate a movie or update an existing rating. This endpoint processes ratings asynchronously.
    
    **Features:**
    - Async processing (returns immediately, updates in background)
    - Rating validation (0-5 stars in 0.5 increments)
    - Upsert functionality (creates new rating or updates existing)
    
    **Request Body:**
    ```json
    {
      "clerk_user_id": "user_2abc123def456",
      "movie_id": 12345,
      "rating": 4.5
    }
    ```
    
    **Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    - `movie_id` (integer): The movie ID to rate
    - `rating` (float): Rating from 0 to 5 (in 0.5 increments)
    
    **Response:**
    ```json
    {
      "message": "Rating update initiated",
      "clerk_user_id": "user_2abc123def456",
      "movie_id": 12345,
      "rating": 4.5,
      "status": "processing"
    }
    ```
    
    **Validation Rules:**
    - Rating must be between 0 and 5
    - Rating must be in 0.5 increments (0, 0.5, 1.0, 1.5, etc.)
    
    **Error Responses:**
    - `400 Bad Request`: Invalid rating value
    - `500 Internal Server Error`: Database or processing error
    """
    try:
        # Validate rating
        if rating_request.rating < 0 or rating_request.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
        
        if (rating_request.rating * 10) % 5 != 0:
            raise HTTPException(status_code=400, detail="Rating must be in 0.5 steps (0, 0.5, 1.0, etc.)")
        
        # Start background task
        asyncio.create_task(update_user_rating_async(
            rating_request.clerk_user_id, 
            rating_request.movie_id, 
            rating_request.rating
        ))
        
        return {
            "message": "Rating update initiated",
            "clerk_user_id": rating_request.clerk_user_id,
            "movie_id": rating_request.movie_id,
            "rating": rating_request.rating,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing rating: {str(e)}")

@app.delete("/ratings/delete", response_model=Dict, tags=["Ratings"])
async def delete_user_rating(rating_request: UserRatingRequest):
    """
    # Delete User Rating
    Remove a user's rating for a specific movie.
    
    **Request Body:**
    - `clerk_user_id` (string): Clerk user ID
    - `movie_id` (integer): Movie ID
    
    **Response:**
    - `message`: Status message
    - `clerk_user_id`: Clerk user ID
    - `movie_id`: Movie ID
    - `status`: "deleted"
    """
    try:
        delete_query = """
            DELETE FROM user_ratings
            WHERE clerk_user_id = %s AND movie_id = %s
        """
        execute_update(delete_query, (rating_request.clerk_user_id, rating_request.movie_id))
        return {
            "message": "User rating deleted successfully",
            "clerk_user_id": rating_request.clerk_user_id,
            "movie_id": rating_request.movie_id,
            "status": "deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user rating: {str(e)}")

@app.get("/ratings/{clerk_user_id}", response_model=List[UserRatingResponse], tags=["Ratings"])
async def get_user_ratings(clerk_user_id: str):
    """
    # Get User Ratings
    Retrieve all ratings for a specific user, ordered by most recently updated.
    Now includes is_watchlisted field.
    """
    try:
        # Use string formatting with proper escaping for now
        safe_user_id = clerk_user_id.replace("'", "''")  # Escape single quotes
        query = f"""
            SELECT 
                ur.id,
                ur.clerk_user_id,
                ur.movie_id,
                ur.rating,
                DATE_FORMAT(ur.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                DATE_FORMAT(ur.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at,
                m.title as movie_title,
                m.poster_path as movie_poster_path,
                m.overview as movie_overview,
                DATE_FORMAT(m.release_date, '%Y-%m-%d') as movie_release_date,
                m.original_language as movie_original_language,
                m.popularity as movie_popularity,
                m.vote_count as movie_vote_count,
                m.vote_average as movie_vote_average,
                CASE 
                    WHEN w.id IS NOT NULL THEN TRUE 
                    ELSE FALSE 
                END AS is_watchlisted
            FROM user_ratings ur
            LEFT JOIN movies m 
                ON ur.movie_id = m.id
            LEFT JOIN watchlist w 
                ON ur.movie_id = w.movie_id AND ur.clerk_user_id = w.clerk_user_id
            WHERE ur.clerk_user_id = '{safe_user_id}'
            ORDER BY ur.updated_at DESC
            LIMIT 40
        """
        rows = execute_query(query)
        # Ensure is_watchlisted is a boolean in the response
        for row in rows:
            row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ============================================================================
# WATCHLIST ENDPOINTS
# ============================================================================

@app.post("/watchlist", response_model=dict, tags=["Watchlist"])
async def add_to_watchlist(watchlist_request: WatchlistRequest):
    """
    # Add Movie to Watchlist
    
    Add a movie to the user's watchlist. This endpoint processes watchlist updates asynchronously.
    
    **Features:**
    - Async processing (returns immediately, updates in background)
    - Upsert functionality (creates new entry or updates existing)
    - Automatic timestamp tracking
    
    **Request Body:**
    ```json
    {
      "clerk_user_id": "user_2abc123def456",
      "movie_id": 12345
    }
    ```
    
    **Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    - `movie_id` (integer): The movie ID to add to watchlist
    
    **Response:**
    ```json
    {
      "message": "Watchlist update initiated",
      "clerk_user_id": "user_2abc123def456",
      "movie_id": 12345,
      "status": "processing"
    }
    ```
    
    **Use Cases:**
    - Save movies for later viewing
    - Build personal movie queue
    - Track movies of interest
    """
    try:
        # Start background task
        asyncio.create_task(add_to_watchlist_async(
            watchlist_request.clerk_user_id, 
            watchlist_request.movie_id
        ))
        
        return {
            "message": "Watchlist update initiated",
            "clerk_user_id": watchlist_request.clerk_user_id,
            "movie_id": watchlist_request.movie_id,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing watchlist: {str(e)}")

@app.get("/watchlist/{clerk_user_id}", response_model=List[WatchlistResponse], tags=["Watchlist"])
async def get_user_watchlist(clerk_user_id: str):
    """
    # Get User Watchlist
    
    Retrieve all movies in the user's watchlist, ordered by most recently added.
    
    **Features:**
    - Returns user's complete watchlist
    - Includes movie details for each watchlist item
    - Ordered by most recently added first
    - Limited to 40 items for performance
    
    **Path Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    
    **Response:**
    - List of watchlist objects with movie details
    - Each item includes: id, clerk_user_id, movie_id, created_at
    - Movie details: title, poster_path, overview, release_date, original_language, popularity, vote_count, vote_average
    
    **Example Response:**
    ```json
    [
      {
        "id": 1,
        "clerk_user_id": "user_2abc123def456",
        "movie_id": 12345,
        "created_at": "2024-01-15 10:30:00",
        "movie_title": "Amaran",
        "movie_poster_path": "/path/to/poster.jpg",
        "movie_overview": "A thrilling action movie...",
        "movie_release_date": "2024-01-10",
        "movie_original_language": "ta",
        "movie_popularity": 15.5,
        "movie_vote_count": 150,
        "movie_vote_average": 7.2
      }
    ]
    ```
    
    **Use Cases:**
    - Display user's watchlist
    - Show saved movies with details
    - Track watchlist additions
    """
    try:
        # Use string formatting with proper escaping for now
        safe_user_id = clerk_user_id.replace("'", "''")  # Escape single quotes
        query = f"""
            SELECT 
                w.id,
                w.clerk_user_id,
                w.movie_id,
                DATE_FORMAT(w.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                m.title as movie_title,
                m.poster_path as movie_poster_path,
                m.overview as movie_overview,
                DATE_FORMAT(m.release_date, '%Y-%m-%d') as movie_release_date,
                m.original_language as movie_original_language,
                m.popularity as movie_popularity,
                m.vote_count as movie_vote_count,
                m.vote_average as movie_vote_average
            FROM watchlist w
            LEFT JOIN movies m ON w.movie_id = m.id
            WHERE w.clerk_user_id = '{safe_user_id}'
            ORDER BY w.created_at DESC
            LIMIT 40
        """
        return execute_query(query)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.delete("/remove-from-watchlist", response_model=dict, tags=["Watchlist"])
async def remove_from_watchlist(watchlist_request: WatchlistRequest):
    """
    # Remove Movie from Watchlist
    
    Remove a movie from the user's watchlist. This endpoint processes watchlist removals asynchronously.
    
    **Features:**
    - Async processing (returns immediately, updates in background)
    - Safe deletion (no error if movie not in watchlist)
    - Immediate response with processing status
    
    **Request Body:**
    ```json
    {
      "clerk_user_id": "user_2abc123def456",
      "movie_id": 12345
    }
    ```
    
    **Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    - `movie_id` (integer): The movie ID to remove from watchlist
    
    **Response:**
    ```json
    {
      "message": "Watchlist removal initiated",
      "clerk_user_id": "user_2abc123def456",
      "movie_id": 12345,
      "status": "processing"
    }
    ```
    
    **Use Cases:**
    - Remove movies from watchlist
    - Clean up watchlist
    - Update movie preferences
    """
    try:
        # Start background task
        asyncio.create_task(remove_from_watchlist_async(
            watchlist_request.clerk_user_id, 
            watchlist_request.movie_id
        ))
        
        return {
            "message": "Watchlist removal initiated",
            "clerk_user_id": watchlist_request.clerk_user_id,
            "movie_id": watchlist_request.movie_id,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing watchlist removal: {str(e)}")

# ============================================================================
# RECOMMENDATIONS ENDPOINTS
# ============================================================================

@app.get("/recommendations/{clerk_user_id}", response_model=List[MovieRecommendation], tags=["Recommendations"])
async def get_movie_recommendations(
    clerk_user_id: str, 
    watched: Optional[bool] = Query(None, description="Filter by watched status (true=watched, false=unwatched, null=all)"),
    limit: int = Query(40, ge=1, le=100)
):
    """
    # Get Movie Recommendations
    Retrieve personalized movie recommendations for a user based on AI predictions and user preferences.
    Now includes is_watchlisted field.
    """
    try:
        # Build the query based on watched parameter
        if watched is None:
            # Get all recommendations
            query = """
                SELECT 
                    m.id,
                    m.title,
                    m.overview,
                    m.poster_path,
                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                    m.original_language,
                    m.popularity,
                    m.vote_count,
                    m.vote_average,
                    r.predicted_rating,
                    ur.rating as user_rating,
                    CASE 
                        WHEN ur.rating IS NOT NULL THEN SQRT(r.predicted_rating * ur.rating)
                        ELSE (r.predicted_rating )
                    END as predicted_star_rating,
                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM recommendations r 
                JOIN movies m ON r.movie_id = m.id
                LEFT JOIN user_ratings ur ON r.movie_id = ur.movie_id AND r.user_id = ur.clerk_user_id
                LEFT JOIN watchlist w ON r.movie_id = w.movie_id AND r.user_id = w.clerk_user_id
                WHERE r.user_id = %s
                ORDER BY
                (predicted_star_rating + 0.04 * m.vote_average * LOG10(GREATEST(m.vote_count, 1))) DESC
                LIMIT %s
            """
            params = (clerk_user_id, limit)
        else:
            # Filter by watched status based on user_ratings presence
            query = """
                SELECT 
                    m.id,
                    m.title,
                    m.overview,
                    m.poster_path,
                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                    m.original_language,
                    m.popularity,
                    m.vote_count,
                    m.vote_average,
                    r.predicted_rating,
                    ur.rating as user_rating,
                    CASE 
                        WHEN ur.rating IS NOT NULL THEN SQRT(r.predicted_rating  * ur.rating)
                        ELSE (r.predicted_rating)
                    END as predicted_star_rating,
                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM recommendations r 
                JOIN movies m ON r.movie_id = m.id 
                LEFT JOIN user_ratings ur ON r.movie_id = ur.movie_id AND r.user_id = ur.clerk_user_id
                LEFT JOIN watchlist w ON r.movie_id = w.movie_id AND r.user_id = w.clerk_user_id
                WHERE r.user_id = %s AND {watched_filter}
                ORDER BY
                (predicted_star_rating + 0.04 * m.vote_average * LOG10(GREATEST(m.vote_count, 1))) DESC
                LIMIT %s
            """
            watched_filter = "ur.rating IS NOT NULL" if watched else "ur.rating IS NULL"
            query = query.format(watched_filter=watched_filter)
            params = (clerk_user_id, limit)
        rows = execute_query(query, params)
        for row in rows:
            row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

# ============================================================================
# USER SUMMARY ENDPOINTS
# ============================================================================

@app.get("/user_summary/{clerk_user_id}", response_model=UserSummary, tags=["User Summary"])
async def get_user_summary(clerk_user_id: str):
    """
    # Get User Summary
    
    Retrieve user preferences summary from the user_preferences_summary table.
    
    **Features:**
    - Fetches user summary based on Clerk user ID
    - Returns user_id and summary information
    - Simple and fast lookup
    
    **Path Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    
    **Response:**
    - User summary object with user_id and summary
    
    **Example Response:**
    ```json
    {
      "user_id": "user_2abc123def456",
      "summary": "User prefers action movies with high ratings..."
    }
    ```
    
    **Use Cases:**
    - Display user preferences summary
    - Show personalized insights
    - User profile information
    """
    try:
        query = """
            SELECT user_id, summary 
            FROM user_preferences_summary ups 
            WHERE user_id = %s
        """
        result = execute_query(query, (clerk_user_id,))
        
        if not result:
            raise HTTPException(status_code=404, detail="User summary not found")
        
        return result[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user summary: {str(e)}")

# Import the new model
from models import (
    Movie, MovieWithStats, UserRatingRequest, UserRatingResponse,
    WatchlistRequest, WatchlistResponse, MovieRecommendation, UserSummary, PreferenceRecommendation
)

@app.get("/user_preferences_movies/{clerk_user_id}", response_model=List[PreferenceRecommendation], tags=["User Preferences"])
async def get_user_preferences_movies(
    clerk_user_id: str,
    watched: Optional[str] = Query(None, description="Filter by watched status (true/false/None for all)")
):
    """
    # Get Movies Based on User Preferences
    
    Retrieve movies based on user's top preference for each type (cast, crew, genre, keyword) from user_preferences_summary table.
    Returns up to four lists, one per preference type, with descriptive titles.
    
    """
    try:
        # First, get the user preferences
        preferences_query = """
            SELECT 
                Cast_1_name, Cast_1_score, Cast_2_name, Cast_2_score, Cast_3_name, Cast_3_score,
                Crew_1_name, Crew_1_score, Crew_2_name, Crew_2_score, Crew_3_name, Crew_3_score,
                Genre_1_name, Genre_1_score, Genre_2_name, Genre_2_score, Genre_3_name, Genre_3_score,
                Keyword_1_name, Keyword_1_score, Keyword_2_name, Keyword_2_score, Keyword_3_name, Keyword_3_score
            FROM user_preferences_summary 
            WHERE user_id = %s
        """
        preferences = execute_query(preferences_query, (clerk_user_id,))
        
        if not preferences:
            raise HTTPException(status_code=404, detail="No user preferences found")
        
        pref = preferences[0]  # Get the first (and only) row
        
        # Detect available cast/crew tables dynamically
        def detect_table_name(preferred: str, alternative: str) -> str:
            try:
                if execute_query("SHOW TABLES LIKE %s", (preferred,)):
                    return preferred
                if execute_query("SHOW TABLES LIKE %s", (alternative,)):
                    return alternative
            except Exception:
                pass
            return preferred
        
        cast_table_name = detect_table_name('movie_cast', 'tmdb_movie_cast')
        crew_table_name = detect_table_name('movie_crew', 'tmdb_movie_crew')
        
        # Helper to choose the top preference name for a given list of (name, score) pairs
        def select_top_preference(name_score_pairs):
            valid = [(n, s) for (n, s) in name_score_pairs if n and s and s > 0]
            if not valid:
                return None, None
            # Sort by score desc and pick top
            valid.sort(key=lambda x: x[1], reverse=True)
            return valid[0][0], valid[0][1]
        
        # Build category-specific sorted preferences (up to top 3)
        def build_candidates(pairs: list[tuple[str, float]]):
            # Keep only those with names
            named = [(n, s or 0) for (n, s) in pairs if n]
            # Use positives if any; else keep original order (so _1 preferred)
            positives = [(n, s) for (n, s) in named if s > 0]
            if positives:
                return sorted(positives, key=lambda x: x[1], reverse=True)
            # All zero or missing scores → return in given order
            return named

        cast_candidates = build_candidates([
            (pref.get('Cast_1_name'), pref.get('Cast_1_score')),
            (pref.get('Cast_2_name'), pref.get('Cast_2_score')),
            (pref.get('Cast_3_name'), pref.get('Cast_3_score')),
        ])
        
        crew_candidates = build_candidates([
            (pref.get('Crew_1_name'), pref.get('Crew_1_score')),
            (pref.get('Crew_2_name'), pref.get('Crew_2_score')),
            (pref.get('Crew_3_name'), pref.get('Crew_3_score')),
        ])
        
        genre_candidates = build_candidates([
            (pref.get('Genre_1_name'), pref.get('Genre_1_score')),
            (pref.get('Genre_2_name'), pref.get('Genre_2_score')),
            (pref.get('Genre_3_name'), pref.get('Genre_3_score')),
        ])
        
        keyword_candidates = build_candidates([
            (pref.get('Keyword_1_name'), pref.get('Keyword_1_score')),
            (pref.get('Keyword_2_name'), pref.get('Keyword_2_score')),
            (pref.get('Keyword_3_name'), pref.get('Keyword_3_score')),
        ])
        
        results = []
        
        # Utility to add watched filter in a user-specific way
        def append_watched_filter(base_query: str, watched_value: Optional[str], params_list: list) -> tuple[str, list]:
            if watched_value is None:
                return base_query, params_list
            watched_value_lower = watched_value.lower()
            if watched_value_lower == 'true':
                base_query = f"{base_query} AND EXISTS (SELECT 1 FROM user_ratings ur2 WHERE ur2.movie_id = m.id AND ur2.clerk_user_id = %s)"
                params_list.append(clerk_user_id)
            elif watched_value_lower == 'false':
                base_query = f"{base_query} AND NOT EXISTS (SELECT 1 FROM user_ratings ur2 WHERE ur2.movie_id = m.id AND ur2.clerk_user_id = %s)"
                params_list.append(clerk_user_id)
            return base_query, params_list
        
        # Helper to attempt a category with up to 3 candidates
        def try_category(category: str, candidates: list):
            nonlocal results
            added = False
            first_valid_title = None
            for name, score in [(n, s) for (n, s) in candidates if n]:
                # Prepare a fallback-friendly title for the section
                if not first_valid_title:
                    if category == 'crew' and '(' in name and ')' in name:
                        name_part = name.split('(')[0].strip()
                        job_part = name.split('(')[1].split(')')[0].strip()
                        first_valid_title = f"Because you like {name_part} ({job_part})"
                    else:
                        first_valid_title = f"Because you like {name} ({category.capitalize()})"
                try:
                    if category == 'cast':
                        query = f"""
                            SELECT 
                                m.id,
                                m.title,
                                m.overview,
                                m.poster_path,
                                COALESCE(m.popularity, 0) as popularity,
                                COALESCE(m.vote_count, 0) as vote_count,
                                COALESCE(m.vote_average, 0) as vote_average,
                                DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                            FROM movies m
                            JOIN {cast_table_name} mc ON m.id = mc.movie_id
                            LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                            LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                            WHERE LOWER(mc.name) LIKE %s
                        """
                        params = [clerk_user_id, clerk_user_id, f"%{name.lower()}%"]
                        title = f"Because you like {name} (Cast)"
                        
                        # Apply watched filter and ordering
                        query, params = append_watched_filter(query, watched, params)
                        query = f"{query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
                        movies = execute_query(query, params)
                        if movies:
                            results.append({"title": title, "movies": movies})
                            added = True
                            return
                    elif category == 'crew':
                        if '(' in name and ')' in name:
                            name_part = name.split('(')[0].strip()
                            job_part = name.split('(')[1].split(')')[0].strip()
                            query = f"""
                                SELECT 
                                    m.id,
                                    m.title,
                                    m.overview,
                                    m.poster_path,
                                    COALESCE(m.popularity, 0) as popularity,
                                    COALESCE(m.vote_count, 0) as vote_count,
                                    COALESCE(m.vote_average, 0) as vote_average,
                                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                    (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                                FROM movies m
                                JOIN {crew_table_name} mc ON m.id = mc.movie_id
                                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                                WHERE LOWER(mc.name) LIKE %s AND LOWER(mc.job) LIKE %s
                            """
                            params = [clerk_user_id, clerk_user_id, f"%{name_part.lower()}%", f"%{job_part.lower()}%"]
                            title = f"Because you like {name_part} ({job_part})"
                        else:
                            query = f"""
                                SELECT 
                                    m.id,
                                    m.title,
                                    m.overview,
                                    m.poster_path,
                                    COALESCE(m.popularity, 0) as popularity,
                                    COALESCE(m.vote_count, 0) as vote_count,
                                    COALESCE(m.vote_average, 0) as vote_average,
                                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                    (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                                FROM movies m
                                JOIN {crew_table_name} mc ON m.id = mc.movie_id
                                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                                WHERE LOWER(mc.name) LIKE %s
                            """
                            params = [clerk_user_id, clerk_user_id, f"%{name.lower()}%"]
                            title = f"Because you like {name} (Crew)"
                        
                        # Apply watched filter and ordering
                        query, params = append_watched_filter(query, watched, params)
                        query = f"{query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
                        movies = execute_query(query, params)
                        
                        # Fallback: if crew yields nothing, try department column if present
                        if not movies:
                            try:
                                if '(' in name and ')' in name:
                                    name_part = name.split('(')[0].strip().lower()
                                    job_part = name.split('(')[1].split(')')[0].strip().lower()
                                    dept_query = f"""
                                        SELECT 
                                            m.id,
                                            m.title,
                                            m.overview,
                                            m.poster_path,
                                            COALESCE(m.popularity, 0) as popularity,
                                            COALESCE(m.vote_count, 0) as vote_count,
                                            COALESCE(m.vote_average, 0) as vote_average,
                                            DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                            (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                            CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                            CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                                        FROM movies m
                                        JOIN {crew_table_name} mc ON m.id = mc.movie_id
                                        LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                                        LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                                        WHERE LOWER(mc.name) LIKE %s AND LOWER(mc.department) LIKE %s
                                    """
                                    dept_params = [clerk_user_id, clerk_user_id, f"%{name_part}%", f"%{job_part}%"]
                                else:
                                    dept_query = f"""
                                        SELECT 
                                            m.id,
                                            m.title,
                                            m.overview,
                                            m.poster_path,
                                            COALESCE(m.popularity, 0) as popularity,
                                            COALESCE(m.vote_count, 0) as vote_count,
                                            COALESCE(m.vote_average, 0) as vote_average,
                                            DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                            (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                            CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                            CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                                        FROM movies m
                                        JOIN {crew_table_name} mc ON m.id = mc.movie_id
                                        LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                                        LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                                        WHERE LOWER(mc.name) LIKE %s
                                    """
                                    dept_params = [clerk_user_id, clerk_user_id, f"%{name.lower()}%"]
                                dept_query, dept_params = append_watched_filter(dept_query, watched, dept_params)
                                dept_query = f"{dept_query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
                                movies = execute_query(dept_query, dept_params)
                            except Exception:
                                pass
                        
                        # Fallback: if crew yields nothing, try matching by cast name
                        if not movies:
                            fallback_query = f"""
                                SELECT 
                                    m.id,
                                    m.title,
                                    m.overview,
                                    m.poster_path,
                                    COALESCE(m.popularity, 0) as popularity,
                                    COALESCE(m.vote_count, 0) as vote_count,
                                    COALESCE(m.vote_average, 0) as vote_average,
                                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                    (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                                FROM movies m
                                JOIN {cast_table_name} mc ON m.id = mc.movie_id
                                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                                WHERE LOWER(mc.name) LIKE %s
                            """
                            fallback_params = [clerk_user_id, clerk_user_id, f"%{name.lower()}%"]
                            fallback_query, fallback_params = append_watched_filter(fallback_query, watched, fallback_params)
                            fallback_query = f"{fallback_query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
                            movies = execute_query(fallback_query, fallback_params)
                        
                        if movies:
                            results.append({"title": title, "movies": movies})
                            added = True
                            return
                    elif category == 'genre':
                        query = """
                            SELECT 
                                m.id,
                                m.title,
                                m.overview,
                                m.poster_path,
                                COALESCE(m.popularity, 0) as popularity,
                                COALESCE(m.vote_count, 0) as vote_count,
                                COALESCE(m.vote_average, 0) as vote_average,
                                DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                            FROM movies m
                            JOIN tmdb_movie_genres mg ON m.id = mg.movie_id
                            LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                            LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                            WHERE mg.tmdb_genres LIKE %s
                        """
                        params = [clerk_user_id, clerk_user_id, f"%{name}%"]
                        title = f"Because you like {name} (Genre)"
                        
                        query, params = append_watched_filter(query, watched, params)
                        query = f"{query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
                        movies = execute_query(query, params)
                        if movies:
                            results.append({"title": title, "movies": movies})
                            added = True
                            return
                    elif category == 'keyword':
                        # Support comma-separated keywords (match any token)
                        terms = [t.strip().lower() for t in (name or '').split(',') if t.strip()]
                        if not terms:
                            terms = [(name or '').lower()]
                        base = """
                            SELECT 
                                m.id,
                                m.title,
                                m.overview,
                                m.poster_path,
                                COALESCE(m.popularity, 0) as popularity,
                                COALESCE(m.vote_count, 0) as vote_count,
                                COALESCE(m.vote_average, 0) as vote_average,
                                DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                                (COALESCE(m.popularity, 0) * COALESCE(m.vote_count, 0) * COALESCE(m.vote_average, 0)) as popularity_score,
                                CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END AS watched,
                                CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                            FROM movies m
                            LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                            LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                            WHERE 
                        """
                        # Build OR conditions for any term in title or overview
                        or_clauses = []
                        like_params = []
                        for t in terms:
                            if not t:
                                continue
                            # Build variants to handle punctuation/spacing differences
                            variants = set()
                            variants.add(t)
                            variants.add(t.replace(' ', '-'))
                            variants.add(t.replace(' ', ''))
                            # wildcard-between-words pattern
                            words = [w for w in t.split(' ') if w]
                            if len(words) > 1:
                                variants.add('%'.join(words))
                            for v in variants:
                                or_clauses.append("LOWER(m.overview) LIKE %s")
                                like_params.append(f"%{v}%")
                                or_clauses.append("LOWER(m.title) LIKE %s")
                                like_params.append(f"%{v}%")
                        if not or_clauses:
                            # Fallback to match anything (should not happen)
                            or_clauses.append("LOWER(m.title) LIKE %s")
                            like_params.append("%%")
                        where_clause = "(" + " OR ".join(or_clauses) + ")"
                        query = base + where_clause
                        params = [clerk_user_id, clerk_user_id] + like_params
                        title = f"Because you like {name} (Keyword)"
                        
                        query, params = append_watched_filter(query, watched, params)
                        query = f"{query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
                        movies = execute_query(query, params)
                        if movies:
                            results.append({"title": title, "movies": movies})
                            added = True
                            return
                except Exception as e:
                    print(f"Warning: Could not query for {category} preference '{name}': {str(e)}")
            
            # If we reach here, no candidate produced movies; still return a section (empty list)
            if first_valid_title is None:
                # If absolutely no valid candidate, create a generic title for the category
                first_valid_title = f"Because you like {category.capitalize()}"
            results.append({"title": first_valid_title, "movies": []})
            return
        
        try_category('cast', cast_candidates)
        try_category('crew', crew_candidates)
        try_category('genre', genre_candidates)
        try_category('keyword', keyword_candidates)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user preferences movies: {str(e)}")

# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@app.get("/debug/ratings-table", tags=["Debug"])
async def debug_ratings_table():
    """
    # Debug Ratings Table
    
    Debug endpoint to check if user_ratings table exists and has data.
    
    **Use Cases:**
    - Verify database table structure
    - Check data availability
    - Troubleshoot rating issues
    
    **Response:**
    ```json
    {
      "table_exists": true,
      "structure": [...],
      "total_records": 150
    }
    ```
    """
    try:
        # Check if table exists
        table_query = "SHOW TABLES LIKE 'user_ratings'"
        table_exists = execute_query(table_query)
        
        if not table_exists:
            return {"error": "user_ratings table does not exist"}
        
        # Check table structure
        structure_query = "DESCRIBE user_ratings"
        structure = execute_query(structure_query)
        
        # Check if there's any data
        count_query = "SELECT COUNT(*) as count FROM user_ratings"
        count = execute_query(count_query)
        
        return {
            "table_exists": True,
            "structure": structure,
            "total_records": count[0]['count'] if count else 0
        }
        
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/debug/watchlist-table", tags=["Debug"])
async def debug_watchlist_table():
    """
    # Debug Watchlist Table
    
    Debug endpoint to check if watchlist table exists and has data.
    
    **Use Cases:**
    - Verify database table structure
    - Check data availability
    - Troubleshoot watchlist issues
    
    **Response:**
    ```json
    {
      "table_exists": true,
      "structure": [...],
      "total_records": 75
    }
    ```
    """
    try:
        # Check if table exists
        table_query = "SHOW TABLES LIKE 'watchlist'"
        table_exists = execute_query(table_query)
        
        if not table_exists:
            return {"error": "watchlist table does not exist"}
        
        # Check table structure
        structure_query = "DESCRIBE watchlist"
        structure = execute_query(structure_query)
        
        # Check if there's any data
        count_query = "SELECT COUNT(*) as count FROM watchlist"
        count = execute_query(count_query)
        
        return {
            "table_exists": True,
            "structure": structure,
            "total_records": count[0]['count'] if count else 0
        }
        
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/debug/user-preferences-table", tags=["Debug"])
async def debug_user_preferences_table():
    """
    # Debug User Preferences Table
    
    Debug endpoint to check if user_preferences_summary table exists and has data.
    
    **Use Cases:**
    - Verify database table structure
    - Check data availability
    - Troubleshoot user preferences issues
    
    **Response:**
    ```json
    {
      "table_exists": true,
      "structure": [...],
      "total_records": 25,
      "sample_data": [...]
    }
    ```
    """
    try:
        # Check if table exists
        table_query = "SHOW TABLES LIKE 'user_preferences_summary'"
        table_exists = execute_query(table_query)
        
        if not table_exists:
            return {"error": "user_preferences_summary table does not exist"}
        
        # Check table structure
        structure_query = "DESCRIBE user_preferences_summary"
        structure = execute_query(structure_query)
        
        # Check if there's any data
        count_query = "SELECT COUNT(*) as count FROM user_preferences_summary"
        count = execute_query(count_query)
        
        # Get sample data
        sample_query = "SELECT * FROM user_preferences_summary LIMIT 5"
        sample_data = execute_query(sample_query)
        
        return {
            "table_exists": True,
            "structure": structure,
            "total_records": count[0]['count'] if count else 0,
            "sample_data": sample_data
        }
        
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/debug/available-tables", tags=["Debug"])
async def debug_available_tables():
    """
    # Debug Available Tables
    
    Debug endpoint to check what tables are available in the database.
    
    **Use Cases:**
    - Verify database table availability
    - Check table names and structure
    - Troubleshoot missing tables
    
    **Response:**
    ```json
    {
      "tables": [...],
      "cast_related": [...],
      "crew_related": [...],
      "genre_related": [...]
    }
    ```
    """
    try:
        # Get all tables
        tables_query = "SHOW TABLES"
        tables = execute_query(tables_query)
        
        # Check for cast-related tables
        cast_tables = []
        crew_tables = []
        genre_tables = []
        
        for table in tables:
            table_name = list(table.values())[0]
            if 'cast' in table_name.lower():
                cast_tables.append(table_name)
            elif 'crew' in table_name.lower():
                crew_tables.append(table_name)
            elif 'genre' in table_name.lower():
                genre_tables.append(table_name)
        
        return {
            "all_tables": [list(table.values())[0] for table in tables],
            "cast_related": cast_tables,
            "crew_related": crew_tables,
            "genre_related": genre_tables
        }
        
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/debug/table-structure/{table_name}", tags=["Debug"])
async def debug_table_structure(table_name: str):
    """
    # Debug Table Structure
    
    Debug endpoint to check the structure of a specific table.
    
    **Use Cases:**
    - Verify table column names
    - Check data types
    - Troubleshoot query issues
    
    **Response:**
    ```json
    {
      "table_name": "movie_cast",
      "structure": [...],
      "sample_data": [...]
    }
    ```
    """
    try:
        # Check table structure
        structure_query = f"DESCRIBE {table_name}"
        structure = execute_query(structure_query)
        
        # Get sample data
        sample_query = f"SELECT * FROM {table_name} LIMIT 3"
        sample_data = execute_query(sample_query)
        
        return {
            "table_name": table_name,
            "structure": structure,
            "sample_data": sample_data
        }
        
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/movie/{movie_id}", response_model=MovieWithStats, tags=["Movies"])
def get_movie_by_id(
    movie_id: int,
    clerk_user_id: Optional[str] = Query(None, description="Clerk user ID for user-specific info")
):
    """
    Get a single movie by its ID. Returns the same fields as the movies listing API.
    If clerk_user_id is provided, includes watched, user_rating, and is_watchlisted fields if present.
    """
    try:
        if clerk_user_id:
            query = """
                SELECT m.id, m.title, m.overview, m.poster_path,
                       COALESCE(m.popularity, 0) as popularity,
                       COALESCE(m.vote_count, 0) as vote_count,
                       COALESCE(m.vote_average, 0) as vote_average,
                       DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                       (COALESCE(m.popularity, 0) + COALESCE(m.vote_count, 0) + COALESCE(m.vote_average, 0)) as popularity_score,
                       ur.rating as user_rating,
                       CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                       CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM movies m
                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                WHERE m.id = %s
                LIMIT 1
            """
            rows = execute_query(query, (clerk_user_id, clerk_user_id, movie_id))
        else:
            query = """
                SELECT id, title, overview, poster_path, popularity, vote_count, vote_average, DATE_FORMAT(release_date, '%Y-%m-%d') as release_date, (COALESCE(popularity, 0) + COALESCE(vote_count, 0) + COALESCE(vote_average, 0)) as popularity_score
                FROM movies 
                WHERE id = %s
                LIMIT 1
            """
            rows = execute_query(query, (movie_id,))
        if not rows:
            raise HTTPException(status_code=404, detail=f"Movie with id {movie_id} not found")
        row = rows[0]
        row["watched"] = bool(row.get("watched", 0))
        row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.post("/semantic-search", response_model=List[SemanticMovieResult], tags=["Movies"])
async def semantic_movie_search(
    search_request: SemanticSearchRequest,
    clerk_user_id: Optional[str] = Query(None, description="Clerk user ID for user-specific info")
):
    """
    # Semantic Movie Search
    
    Find movies similar to a given description using embeddings and cosine similarity.
    Uses database-level cosine similarity function for efficient calculation.
    
    **Features:**
    - Converts user description to embeddings
    - Uses MySQL COSINE_SIMILARITY function for fast similarity calculation
    - Returns top 10 most similar movies
    - Includes user-specific info if clerk_user_id provided
    
    **Request Body:**
    ```json
    {
      "description": "A thrilling action movie with car chases and explosions"
    }
    ```
    
    **Parameters:**
    - `description` (string): Movie description to search for
    - `clerk_user_id` (optional): Clerk user ID for user-specific info
    
    **Response:**
    - List of movies with similarity scores
    - Each movie includes: id, title, overview, poster_path, release_date, 
      original_language, popularity, vote_count, vote_average, similarity_score
    - If clerk_user_id provided: user_rating, watched, is_watchlisted
    """
    try:
        # Load the embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate embedding for the search description
        search_embedding = model.encode(search_request.description)
        search_embedding_json = json.dumps(search_embedding.tolist())
        
        # Build the query using the COSINE_SIMILARITY function
        if clerk_user_id:
            query = """
                SELECT 
                    m.id,
                    m.title,
                    m.overview,
                    m.poster_path,
                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                    m.original_language,
                    m.popularity,
                    m.vote_count,
                    m.vote_average,
                    ur.rating as user_rating,
                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted,
                    COSINE_SIMILARITY(me.embedding_vector, %s) as similarity_score
                FROM movies m
                JOIN movie_embeddings me ON m.id = me.movie_id
                LEFT JOIN user_ratings ur ON m.id = ur.movie_id AND ur.clerk_user_id = %s
                LEFT JOIN watchlist w ON m.id = w.movie_id AND w.clerk_user_id = %s
                WHERE me.embedding_vector IS NOT NULL
                HAVING similarity_score IS NOT NULL
                ORDER BY similarity_score DESC
                LIMIT 10
            """
            params = (search_embedding_json, clerk_user_id, clerk_user_id)
        else:
            query = """
                SELECT 
                    m.id,
                    m.title,
                    m.overview,
                    m.poster_path,
                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                    m.original_language,
                    m.popularity,
                    m.vote_count,
                    m.vote_average,
                    COSINE_SIMILARITY(me.embedding_vector, %s) as similarity_score
                FROM movies m
                JOIN movie_embeddings me ON m.id = me.movie_id
                WHERE me.embedding_vector IS NOT NULL
                HAVING similarity_score IS NOT NULL
                ORDER BY similarity_score DESC
                LIMIT 10
            """
            params = (search_embedding_json,)
        
        rows = execute_query(query, params)
        
        if not rows:
            raise HTTPException(status_code=404, detail="No movie embeddings found in database")
        
        # Format results
        results = []
        for row in rows:
            result = {
                'id': row['id'],
                'title': row['title'],
                'overview': row['overview'],
                'poster_path': row['poster_path'],
                'release_date': row['release_date'],
                'original_language': row['original_language'],
                'popularity': float(row['popularity'] or 0),
                'vote_count': int(row['vote_count'] or 0),
                'vote_average': float(row['vote_average'] or 0),
                'similarity_score': float(row['similarity_score'] or 0)
            }
            
            if clerk_user_id:
                result['user_rating'] = row.get('user_rating')
                result['watched'] = bool(row.get('watched', 0))
                result['is_watchlisted'] = bool(row.get('is_watchlisted', False))
            else:
                result['user_rating'] = None
                result['watched'] = None
                result['is_watchlisted'] = False
            
            results.append(result)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in semantic search: {str(e)}")

@app.get("/filters/cast/autocomplete", response_model=List[str], tags=["Filters"])
async def autocomplete_cast(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    try:
        # Prefer detected cast table if available
        table = "movie_cast"
        try:
            if not execute_query("SHOW TABLES LIKE 'movie_cast'") and execute_query("SHOW TABLES LIKE 'tmdb_movie_cast'"):
                table = "tmdb_movie_cast"
        except Exception:
            pass
        query = f"""
            SELECT mc.name
            FROM {table} mc
            WHERE mc.name LIKE %s
            GROUP BY mc.name
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        rows = execute_query(query, (f"%{q}%", limit))
        return [r['name'] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cast autocomplete: {str(e)}")

@app.get("/filters/crew/autocomplete", response_model=List[str], tags=["Filters"])
async def autocomplete_crew(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    try:
        table = "movie_crew"
        try:
            if not execute_query("SHOW TABLES LIKE 'movie_crew'") and execute_query("SHOW TABLES LIKE 'tmdb_movie_crew'"):
                table = "tmdb_movie_crew"
        except Exception:
            pass
        query = f"""
            SELECT mc.name
            FROM {table} mc
            WHERE mc.name LIKE %s
            GROUP BY mc.name
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """
        rows = execute_query(query, (f"%{q}%", limit))
        return [r['name'] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting crew autocomplete: {str(e)}")

@app.get("/filters/genres", response_model=List[str], tags=["Filters"])
async def list_genres(limit: int = Query(100, ge=1, le=500)):
    try:
        # Pull genre arrays and extract individual items
        rows = execute_query("SELECT tmdb_genres FROM tmdb_movie_genres LIMIT 1000")
        seen = set()
        for row in rows:
            raw = row.get('tmdb_genres')
            if raw is None:
                continue
            try:
                # Try parse as JSON array: ["adventure", "action", ...]
                if isinstance(raw, str):
                    parsed = json.loads(raw)
                else:
                    parsed = raw
                if isinstance(parsed, list):
                    for g in parsed:
                        if isinstance(g, str) and g.strip():
                            seen.add(g.strip())
                    continue
            except Exception:
                pass
            # Fallback: treat as comma-separated string
            text = str(raw)
            # Remove brackets/quotes if present
            text = text.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
            parts = [p.strip() for p in text.split(',') if p.strip()]
            for p in parts:
                seen.add(p)
        genres = sorted(seen)
        return genres[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing genres: {str(e)}")

@app.get("/filters/languages", response_model=List[str], tags=["Filters"])
async def list_languages(limit: int = Query(50, ge=1, le=200)):
    try:
        rows = execute_query("SELECT DISTINCT original_language FROM movies WHERE original_language IS NOT NULL AND original_language<>'' ORDER BY original_language ASC LIMIT %s", (limit,))
        return [r['original_language'] for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing languages: {str(e)}")

@app.get("/recommendations_filtered", response_model=List[MovieRecommendation], tags=["Recommendations"])
async def get_filtered_recommendations(
    clerk_user_id: str,
    cast: Optional[List[str]] = Query(None, description="Cast names to include"),
    crew: Optional[List[str]] = Query(None, description="Crew names to include"),
    genres: Optional[List[str]] = Query(None, description="Genres to include"),
    languages: Optional[List[str]] = Query(None, description="Original languages (e.g., ta, te)"),
    watched: Optional[bool] = Query(None, description="true for watched only, false for unwatched only"),
    semantic_query: Optional[str] = Query(None, description="Free-text semantic search to boost/filter"),
    limit: int = Query(40, ge=1, le=100)
):
    try:
        def build_and_execute(
            include_cast: bool,
            include_crew: bool,
            include_genres: bool,
            include_languages: bool,
            include_watched: bool,
            use_primary_semantic: bool
        ):
            
            print(f"[filtered] attempt: cast={include_cast} crew={include_crew} genres={include_genres} langs={include_languages} watched={include_watched} semantic={'primary' if semantic_query and use_primary_semantic else ('fallback' if semantic_query and not use_primary_semantic else 'off')}", flush=True)
            joins = [
                "FROM recommendations r",
                "JOIN movies m ON r.movie_id = m.id",
                "LEFT JOIN user_ratings ur ON r.movie_id = ur.movie_id AND r.user_id = ur.clerk_user_id",
                "LEFT JOIN watchlist w ON r.movie_id = w.movie_id AND r.user_id = w.clerk_user_id"
            ]
            where_clauses = ["r.user_id = %s"]
            params_local: List = [clerk_user_id]

            # Optional joins/filters
            if include_cast and cast:
                cast_table = 'movie_cast'
                try:
                    if not execute_query("SHOW TABLES LIKE 'movie_cast'") and execute_query("SHOW TABLES LIKE 'tmdb_movie_cast'"):
                        cast_table = 'tmdb_movie_cast'
                except Exception:
                    pass
                joins.append(f"JOIN {cast_table} mcF ON m.id = mcF.movie_id")
                or_count = len(cast)
                for name in cast:
                    params_local.append(f"%{name.lower()}%")
                where_clauses.append("(" + " OR ".join(["LOWER(mcF.name) LIKE %s"]*or_count) + ")")

            if include_crew and crew:
                crew_table = 'movie_crew'
                try:
                    if not execute_query("SHOW TABLES LIKE 'movie_crew'") and execute_query("SHOW TABLES LIKE 'tmdb_movie_crew'"):
                        crew_table = 'tmdb_movie_crew'
                except Exception:
                    pass
                joins.append(f"JOIN {crew_table} crF ON m.id = crF.movie_id")
                or_count = len(crew)
                for name in crew:
                    params_local.append(f"%{name.lower()}%")
                where_clauses.append("(" + " OR ".join(["LOWER(crF.name) LIKE %s"]*or_count) + ")")

            if include_genres and genres:
                joins.append("JOIN tmdb_movie_genres mgF ON m.id = mgF.movie_id")
                or_count = len(genres)
                for g in genres:
                    params_local.append(f"%{g.lower()}%")
                where_clauses.append("(" + " OR ".join(["LOWER(mgF.tmdb_genres) LIKE %s"]*or_count) + ")")

            if include_languages and languages:
                or_count = len(languages)
                placeholders = ",".join(["%s"]*or_count)
                where_clauses.append(f"m.original_language IN ({placeholders})")
                for lang in languages:
                    params_local.append(lang)

            # Semantic search optional join
            semantic_threshold_primary = 0.5
            semantic_threshold_fallback = 0.3
            embedding_json = None
            similarity_select = ""
            having_clause = ""
            params_with_sem = list(params_local)
            if semantic_query:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                emb = model.encode(semantic_query)
                embedding_json = json.dumps(emb.tolist())
                joins.append("JOIN movie_embeddings me ON m.id = me.movie_id")
                similarity_select = ", COSINE_SIMILARITY(me.embedding_vector, %s) as similarity_score"
                having_clause = " HAVING similarity_score >= %s"
                params_with_sem.append(embedding_json)
                params_with_sem.append(semantic_threshold_primary if use_primary_semantic else semantic_threshold_fallback)

            # Watched filter
            if include_watched and watched is True:
                where_clauses.append("ur.rating IS NOT NULL")
            elif include_watched and watched is False:
                where_clauses.append("ur.rating IS NULL")

            select = """
                SELECT 
                    m.id,
                    m.title,
                    m.overview,
                    m.poster_path,
                    DATE_FORMAT(m.release_date, '%Y-%m-%d') as release_date,
                    m.original_language,
                    m.popularity,
                    m.vote_count,
                    m.vote_average,
                    r.predicted_rating,
                    ur.rating as user_rating,
                    CASE 
                        WHEN ur.rating IS NOT NULL THEN SQRT(r.predicted_rating * ur.rating)
                        ELSE (r.predicted_rating)
                    END as predicted_star_rating,
                    CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE 0 END as watched,
                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
            """

            query_local = select + similarity_select + "\n" + "\n".join(joins)
            if where_clauses:
                query_local += "\nWHERE " + " AND ".join(where_clauses)
            if semantic_query:
                query_local += having_clause
            query_local += "\nORDER BY (predicted_star_rating + 0.04 * m.vote_average * LOG10(GREATEST(m.vote_count, 1))) DESC\nLIMIT %s"

            exec_params = tuple(params_with_sem + [limit])
           
            result_rows = execute_query(query_local, exec_params)
            logger.info("[filtered] rows returned=%d", len(result_rows) if result_rows else 0)
            
            return result_rows

        # First attempt with all provided filters and semantic primary threshold
        rows = build_and_execute(
            include_cast=True,
            include_crew=True,
            include_genres=True,
            include_languages=True,
            include_watched=True,
            use_primary_semantic=True
        )

        # Semantic fallback if needed
        if semantic_query and not rows:
            logger.info("[filtered] empty on primary threshold; trying semantic fallback threshold")
            rows = build_and_execute(
                include_cast=True,
                include_crew=True,
                include_genres=True,
                include_languages=True,
                include_watched=True,
                use_primary_semantic=False
            )

        # Progressive relaxation on empty
        if not rows:
            logger.info("[filtered] empty; dropping watched filter")
           
            # Drop watched
            rows = build_and_execute(True, True, True, True, False, True)
        if semantic_query and not rows:
            logger.info("[filtered] still empty; try with semantic fallback without watched")
            rows = build_and_execute(True, True, True, True, False, False)
        if not rows:
            logger.info("[filtered] still empty; dropping genres")
            # Drop genres
            rows = build_and_execute(True, True, False, True, False, True)
        if semantic_query and not rows:
            logger.info("[filtered] still empty; genres dropped with semantic fallback")
            rows = build_and_execute(True, True, False, True, False, False)
        if not rows:
            logger.info("[filtered] still empty; dropping languages")
            # Drop languages
            rows = build_and_execute(True, True, False, False, False, True)
        if semantic_query and not rows:
            logger.info("[filtered] still empty; languages dropped with semantic fallback")
            rows = build_and_execute(True, True, False, False, False, False)
        if not rows:
            logger.info("[filtered] still empty; dropping cast")
            # Drop cast
            rows = build_and_execute(False, True, False, False, False, True)
        if semantic_query and not rows:
            logger.info("[filtered] still empty; cast dropped with semantic fallback")
            rows = build_and_execute(False, True, False, False, False, False)
        if not rows:
            logger.info("[filtered] still empty; dropping crew")
            # Drop crew
            rows = build_and_execute(False, False, False, False, False, True)
        if semantic_query and not rows:
            logger.info("[filtered] still empty; crew dropped with semantic fallback")
            rows = build_and_execute(False, False, False, False, False, False)

        for row in rows:
            row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filtered recommendations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 