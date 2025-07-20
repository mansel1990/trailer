from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
import os

# Import our modules
from models import (
    Movie, MovieWithStats, UserRatingRequest, UserRatingResponse,
    WatchlistRequest, WatchlistResponse, MovieRecommendation
)
from database import execute_query
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
# MOVIE ENDPOINTS
# ============================================================================

@app.get("/movies", response_model=List[Movie], tags=["Movies"])
def get_movies():
    """
    # Get Popular Tamil Movies
    
    Retrieve a list of popular Tamil movies, ordered by popularity.
    
    **Features:**
    - Limited to 40 movies for performance
    - Only includes released movies (not upcoming)
    - Ordered by popularity (highest first)
    - Focuses on Tamil language movies
    
    **Response:**
    - List of movie objects with basic information
    - Each movie includes: id, title, overview, poster_path
    
    **Example Response:**
    ```json
    [
      {
        "id": 12345,
        "title": "Amaran",
        "overview": "A thrilling action movie...",
        "poster_path": "/path/to/poster.jpg"
      }
    ]
    ```
    """
    try:
        query = """
            SELECT id, title, overview, poster_path 
            FROM movies 
            WHERE original_language='ta' AND release_date<CURRENT_TIMESTAMP()
            ORDER BY popularity DESC 
            LIMIT 40
        """
        return execute_query(query)
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/movies/popular/recent", response_model=List[MovieWithStats], tags=["Movies"])
def get_recent_popular_movies():
    """
    # Get Recent Popular Movies
    
    Retrieve movies from the last 3 weeks sorted by popularity score.
    
    **Features:**
    - Includes movies from last 3 weeks
    - Multi-language support (Tamil, Telugu, Kannada, Hindi, Malayalam, Bengali)
    - Popularity score calculation: popularity + vote_count + vote_average
    - Ordered by release date (newest first) then popularity
    
    **Response:**
    - List of movie objects with detailed statistics
    - Each movie includes: id, title, overview, poster_path, popularity, vote_count, vote_average, release_date, popularity_score
    
    **Use Cases:**
    - Discover recent releases
    - Find trending movies
    - Browse by popularity metrics
    """
    try:
        query = """
            SELECT 
                id, 
                title, 
                overview, 
                poster_path,
                COALESCE(popularity, 0) as popularity,
                COALESCE(vote_count, 0) as vote_count,
                COALESCE(vote_average, 0) as vote_average,
                DATE_FORMAT(release_date, '%Y-%m-%d') as release_date,
                (COALESCE(popularity, 0) + COALESCE(vote_count, 0) + COALESCE(vote_average, 0)) as popularity_score
            FROM movies 
            WHERE release_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 WEEK)
                AND release_date <= CURRENT_DATE()
            ORDER BY release_date desc, popularity DESC
            LIMIT 40
        """
        return execute_query(query)
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/movies/upcoming", response_model=List[MovieWithStats], tags=["Movies"])
def get_upcoming_movies():
    """
    # Get Upcoming Movies
    
    Retrieve movies that are going to be released in the next 4 weeks.
    
    **Features:**
    - Includes movies releasing in next 4 weeks
    - Multi-language support (Tamil, Telugu, Kannada, Hindi, Malayalam, Bengali)
    - Popularity score calculation: popularity × vote_count × vote_average
    - Ordered by release date (earliest first) then popularity score
    
    **Response:**
    - List of movie objects with detailed statistics
    - Each movie includes: id, title, overview, poster_path, popularity, vote_count, vote_average, release_date, popularity_score
    
    **Use Cases:**
    - Plan movie watching schedule
    - Discover new releases
    - Stay updated with upcoming movies
    """
    try:
        query = """
            SELECT 
                id, 
                title, 
                overview, 
                poster_path,
                COALESCE(popularity, 0) as popularity,
                COALESCE(vote_count, 0) as vote_count,
                COALESCE(vote_average, 0) as vote_average,
                DATE_FORMAT(release_date, '%Y-%m-%d') as release_date,
                (COALESCE(popularity, 0) * COALESCE(vote_count, 0) * COALESCE(vote_average, 0)) as popularity_score
            FROM movies 
            WHERE release_date > CURRENT_DATE()
                AND release_date <= DATE_ADD(CURRENT_DATE(), INTERVAL 4 WEEK)
                AND original_language IN ('ta', 'te', 'kn', 'hi', 'ml', 'bn')
            ORDER BY release_date ASC, (COALESCE(popularity, 0) * COALESCE(vote_count, 0) * COALESCE(vote_average, 0)) DESC
            LIMIT 40
        """
        return execute_query(query)
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

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

@app.get("/ratings/{clerk_user_id}", response_model=List[UserRatingResponse], tags=["Ratings"])
async def get_user_ratings(clerk_user_id: str):
    """
    # Get User Ratings
    
    Retrieve all ratings for a specific user, ordered by most recently updated.
    
    **Features:**
    - Returns user's complete rating history
    - Includes movie details for each rating
    - Shows watchlist status for each rated movie
    - Ordered by most recent updates first
    - Limited to 40 ratings for performance
    
    **Path Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    
    **Response:**
    - List of rating objects with movie details
    - Each rating includes: id, clerk_user_id, movie_id, rating, created_at, updated_at
    - Movie details: title, poster_path, overview, release_date, original_language, popularity, vote_count, vote_average
    - Watchlist status: is_watchlisted (boolean)
    
    **Example Response:**
    ```json
    [
      {
        "id": 1,
        "clerk_user_id": "user_2abc123def456",
        "movie_id": 12345,
        "rating": 4.5,
        "created_at": "2024-01-15 10:30:00",
        "updated_at": "2024-01-15 10:30:00",
        "movie_title": "Amaran",
        "movie_poster_path": "/path/to/poster.jpg",
        "movie_overview": "A thrilling action movie...",
        "movie_release_date": "2024-01-10",
        "movie_original_language": "ta",
        "movie_popularity": 15.5,
        "movie_vote_count": 150,
        "movie_vote_average": 7.2,
        "is_watchlisted": true
      }
    ]
    ```
    
    **Use Cases:**
    - Display user's rating history
    - Show rated movies with details
    - Track rating patterns
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
        return execute_query(query)
        
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
    
    **Features:**
    - AI-powered recommendations using predicted scores
    - Filter by watched/unwatched status
    - Customizable result limit
    - Multi-language movie support
    - Final score calculation: predicted_score × 5 × popularity × vote_average
    
    **Path Parameters:**
    - `clerk_user_id` (string): Your Clerk user ID
    
    **Query Parameters:**
    - `watched` (optional boolean): Filter recommendations
      - `true`: Only watched movies
      - `false`: Only unwatched movies  
      - `null` (default): All recommendations
    - `limit` (integer, 1-100): Number of recommendations to return (default: 40)
    
    **Response:**
    - List of movie recommendation objects
    - Each recommendation includes: id, title, overview, poster_path, release_date, original_language, popularity, vote_count, vote_average, predicted_score, final_score, watched
    
    **Example Response:**
    ```json
    [
      {
        "id": 12345,
        "title": "Amaran",
        "overview": "A thrilling action movie...",
        "poster_path": "/path/to/poster.jpg",
        "release_date": "2024-01-10",
        "original_language": "ta",
        "popularity": 15.5,
        "vote_count": 150,
        "vote_average": 7.2,
        "predicted_score": 0.85,
        "final_score": 172.82,
        "watched": false
      }
    ]
    ```
    
    **Use Cases:**
    - Discover new movies based on preferences
    - Get personalized recommendations
    - Filter recommendations by watch status
    - Build recommendation engines
    
    **Algorithm:**
    - Uses machine learning predictions from `recommendations_movie` table
    - Combines predicted scores with movie popularity metrics
    - Orders by final score for optimal recommendations
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
                    m.popularity/10 as popularity,
                    m.vote_count,
                    m.vote_average*3 as vote_average,
                    rm.predicted_score,
                    (rm.predicted_score * 5 * popularity * vote_average) as final_score,
                    (rm.predicted_score * 5) as predicted_star_rating,
                    rm.watched
                FROM recommendations_movie rm 
                JOIN movies m ON rm.movie_id = m.id
                WHERE rm.clerk_user_id = %s
                ORDER BY (rm.predicted_score * 5) DESC
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
                    SQRT(rm.predicted_score * 5 * ur.rating) as predicted_star_rating,
                    rm.watched
                FROM recommendations_movie rm 
                JOIN movies m ON rm.movie_id = m.id 
                join user_ratings ur on rm.movie_id = ur.movie_id and rm.clerk_user_id = ur.clerk_user_id
                WHERE rm.clerk_user_id = %s AND rm.watched = %s
                ORDER BY user_rating DESC, predicted_star_rating DESC;
                LIMIT %s
            """
            params = (clerk_user_id, watched, limit)
        
        return execute_query(query, params)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 