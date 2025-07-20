from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import asyncio
import os

# Import our modules
from models import (
    Movie, MovieWithStats, UserRatingRequest, UserRatingResponse,
    WatchlistRequest, WatchlistResponse, MovieRecommendation, UserSummary, LoginRequest
)
from database import execute_query, execute_update
from services import (
    update_user_rating_async, add_to_watchlist_async, remove_from_watchlist_async
)

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
                       COALESCE(rm.predicted_score, 0) as predicted_score,
                       ur.rating as user_rating,
                       CASE WHEN ur.rating IS NOT NULL THEN 1 ELSE COALESCE(rm.watched, 0) END as watched,
                       CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted,
                       CASE WHEN ur.rating IS NOT NULL THEN SQRT(COALESCE(rm.predicted_score, 0) * 5 * ur.rating)
                            ELSE (COALESCE(rm.predicted_score, 0) * 5)
                       END as predicted_star_rating
                FROM movies m
                LEFT JOIN recommendations_movie rm ON m.id = rm.movie_id AND rm.clerk_user_id = %s
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
                row["predicted_score"] = row.get("predicted_score", 0.0)
                row["predicted_star_rating"] = row.get("predicted_star_rating", 0.0)
                row["user_rating"] = row.get("user_rating")
                row["watched"] = bool(row.get("watched", 0))
                row["is_watchlisted"] = bool(row.get("is_watchlisted", False))
            else:
                row["predicted_score"] = 0.0
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
    limit: int = Query(40, ge=1, le=100, description="Number of recommendations to return (1-100)")
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
                    rm.predicted_score,
                    ur.rating as user_rating,
                    CASE 
                        WHEN ur.rating IS NOT NULL THEN SQRT(rm.predicted_score * 5 * ur.rating)
                        ELSE (rm.predicted_score * 5)
                    END as predicted_star_rating,
                    rm.watched,
                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM recommendations_movie rm 
                JOIN movies m ON rm.movie_id = m.id
                LEFT JOIN user_ratings ur ON rm.movie_id = ur.movie_id AND rm.clerk_user_id = ur.clerk_user_id
                LEFT JOIN watchlist w ON rm.movie_id = w.movie_id AND rm.clerk_user_id = w.clerk_user_id
                WHERE rm.clerk_user_id = %s
                ORDER BY predicted_star_rating DESC
                LIMIT %s
            """
            params = (clerk_user_id, limit)
        else:
            # Filter by watched status
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
                    rm.predicted_score,
                    ur.rating as user_rating,
                    CASE 
                        WHEN ur.rating IS NOT NULL THEN SQRT(rm.predicted_score * 5 * ur.rating)
                        ELSE (rm.predicted_score * 5)
                    END as predicted_star_rating,
                    rm.watched,
                    CASE WHEN w.id IS NOT NULL THEN TRUE ELSE FALSE END as is_watchlisted
                FROM recommendations_movie rm 
                JOIN movies m ON rm.movie_id = m.id 
                left join user_ratings ur on rm.movie_id = ur.movie_id and rm.clerk_user_id = ur.clerk_user_id
                LEFT JOIN watchlist w ON rm.movie_id = w.movie_id AND rm.clerk_user_id = w.clerk_user_id
                WHERE rm.clerk_user_id = %s AND rm.watched = %s
                ORDER BY predicted_star_rating DESC
                LIMIT %s
            """
            params = (clerk_user_id, watched, limit)
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
    
    Retrieve movies based on user's top 3 preferences from user_preferences_summary table.
    Returns separate lists for each preference type with descriptive titles.
    
    **Features:**
    - Gets top 3 highest scoring preferences for each category
    - Searches movies based on preference type:
      - **Cast**: Movies where the cast member appears (from movie_cast table)
      - **Crew**: Movies where crew member has the specified job role (from movie_crew table)
      - **Keyword**: Movies where keyword appears in overview
      - **Genre**: Movies with matching genre (from tmdb_movie_genres table)
    - Returns separate lists for each preference type
    - Orders results by popularity × vote_average (descending)
    - Includes watched status for each movie
    - Optional watched filter (true/false/None)
    
    **Path Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    
    **Query Parameters:**
    - `watched` (optional string): Filter by watched status
      - `true`: Only watched movies
      - `false`: Only unwatched movies
      - `None` (default): All movies
    
    **Response:**
    - List of preference recommendation objects
    - Each object includes: title (descriptive reason) and movies list
    - Each movie includes: id, title, overview, poster_path, popularity, vote_count, vote_average, release_date, popularity_score, watched
    
    **Example Response:**
    ```json
    [
      {
        "title": "Because you like Karthi (Cast)",
        "movies": [
          {
            "id": 12345,
            "title": "Amaran",
            "overview": "A thrilling action movie...",
            "poster_path": "/path/to/poster.jpg",
            "popularity": 15.5,
            "vote_count": 150,
            "vote_average": 7.2,
                    "release_date": "2024-01-10",
        "popularity_score": 16740.0,
        "watched": false
      }
    ]
  }
]
```
    
    **Use Cases:**
    - Personalized movie recommendations
    - Discover movies based on user preferences
    - Filter by watch status
    - Build preference-based recommendation engine
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
        
        # Collect all preferences and sort by score
        all_preferences = []
        
        # Process cast preferences
        cast_prefs = [
            (pref['Cast_1_name'], pref['Cast_1_score'], 'cast'),
            (pref['Cast_2_name'], pref['Cast_2_score'], 'cast'),
            (pref['Cast_3_name'], pref['Cast_3_score'], 'cast')
        ]
        all_preferences.extend([(name, score, 'cast') for name, score, _ in cast_prefs if name and score > 0])
        
        # Process crew preferences
        crew_prefs = [
            (pref['Crew_1_name'], pref['Crew_1_score'], 'crew'),
            (pref['Crew_2_name'], pref['Crew_2_score'], 'crew'),
            (pref['Crew_3_name'], pref['Crew_3_score'], 'crew')
        ]
        all_preferences.extend([(name, score, 'crew') for name, score, _ in crew_prefs if name and score > 0])
        
        # Process genre preferences
        genre_prefs = [
            (pref['Genre_1_name'], pref['Genre_1_score'], 'genre'),
            (pref['Genre_2_name'], pref['Genre_2_score'], 'genre'),
            (pref['Genre_3_name'], pref['Genre_3_score'], 'genre')
        ]
        all_preferences.extend([(name, score, 'genre') for name, score, _ in genre_prefs if name and score > 0])
        
        # Process keyword preferences
        keyword_prefs = [
            (pref['Keyword_1_name'], pref['Keyword_1_score'], 'keyword'),
            (pref['Keyword_2_name'], pref['Keyword_2_score'], 'keyword'),
            (pref['Keyword_3_name'], pref['Keyword_3_score'], 'keyword')
        ]
        all_preferences.extend([(name, score, 'keyword') for name, score, _ in keyword_prefs if name and score > 0])
        
        # Sort by score and take top 3
        all_preferences.sort(key=lambda x: x[1], reverse=True)
        top_3_preferences = all_preferences[:3]
        
        results = []
        
        for pref_name, pref_score, pref_type in top_3_preferences:
            # Build query based on preference type
            if pref_type == 'cast':
                # Search in movies_cast table
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
                        CASE 
                            WHEN rm.watched IS NOT NULL THEN rm.watched 
                            ELSE FALSE 
                        END AS watched
                    FROM movies m
                    JOIN movie_cast mc ON m.id = mc.movie_id
                    LEFT JOIN recommendations_movie rm ON m.id = rm.movie_id AND rm.clerk_user_id = %s
                    WHERE mc.name LIKE %s
                """
                params = [clerk_user_id, f"%{pref_name}%"]
                title = f"Because you like {pref_name} (Cast)"
                
            elif pref_type == 'crew':
                # Search in movie_crew table
                if '(' in pref_name and ')' in pref_name:
                    name_part = pref_name.split('(')[0].strip()
                    job_part = pref_name.split('(')[1].split(')')[0].strip()
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
                            CASE 
                                WHEN rm.watched IS NOT NULL THEN rm.watched 
                                ELSE FALSE 
                            END AS watched
                        FROM movies m
                        JOIN movie_crew mc ON m.id = mc.movie_id
                        LEFT JOIN recommendations_movie rm ON m.id = rm.movie_id AND rm.clerk_user_id = %s
                        WHERE mc.name LIKE %s AND mc.job LIKE %s
                    """
                    params = [clerk_user_id, f"%{name_part}%", f"%{job_part}%"]
                    title = f"Because you like {name_part} ({job_part})"
                else:
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
                            CASE 
                                WHEN rm.watched IS NOT NULL THEN rm.watched 
                                ELSE FALSE 
                            END AS watched
                        FROM movies m
                        JOIN movie_crew mc ON m.id = mc.movie_id
                        LEFT JOIN recommendations_movie rm ON m.id = rm.movie_id AND rm.clerk_user_id = %s
                        WHERE mc.name LIKE %s
                    """
                    params = [clerk_user_id, f"%{pref_name}%"]
                    title = f"Because you like {pref_name} (Crew)"
                
            elif pref_type == 'genre':
                # Search in tmdb_movie_genres table
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
                        CASE 
                            WHEN rm.watched IS NOT NULL THEN rm.watched 
                            ELSE FALSE 
                        END AS watched
                    FROM movies m
                    JOIN tmdb_movie_genres mg ON m.id = mg.movie_id
                    LEFT JOIN recommendations_movie rm ON m.id = rm.movie_id AND rm.clerk_user_id = %s
                    WHERE mg.tmdb_genres LIKE %s
                """
                params = [clerk_user_id, f"%{pref_name}%"]
                title = f"Because you like {pref_name} (Genre)"
                
            elif pref_type == 'keyword':
                # Search in movie overview
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
                        CASE 
                            WHEN rm.watched IS NOT NULL THEN rm.watched 
                            ELSE FALSE 
                        END AS watched
                    FROM movies m
                    LEFT JOIN recommendations_movie rm ON m.id = rm.movie_id AND rm.clerk_user_id = %s
                    WHERE m.overview LIKE %s
                """
                params = [clerk_user_id, f"%{pref_name}%"]
                title = f"Because you like {pref_name} (Keyword)"
            
            # Add watched filter if specified
            if watched is not None:
                if watched.lower() == 'true':
                    query = f"{query} AND EXISTS (SELECT 1 FROM recommendations_movie rm WHERE rm.movie_id = m.id AND rm.watched = 1)"
                elif watched.lower() == 'false':
                    query = f"{query} AND EXISTS (SELECT 1 FROM recommendations_movie rm WHERE rm.movie_id = m.id AND rm.watched = 0)"
            
            # Add ordering and limit
            query = f"{query} ORDER BY (popularity * vote_average) DESC LIMIT 20"
            
            # Execute query
            try:
                movies = execute_query(query, params)
                if movies:
                    results.append({
                        "title": title,
                        "movies": movies
                    })
            except Exception as e:
                # If table doesn't exist, skip this preference
                print(f"Warning: Could not query for {pref_type} preference '{pref_name}': {str(e)}")
                continue
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 