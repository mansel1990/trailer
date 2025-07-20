from pydantic import BaseModel
from typing import List, Optional

# Login model
class LoginRequest(BaseModel):
    clerkUserId: str
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    imageUrl: Optional[str] = None
    username: Optional[str] = None

# Basic movie model
class Movie(BaseModel):
    id: int
    title: str
    overview: str
    poster_path: Optional[str] = None

# Movie with statistics
class MovieWithStats(BaseModel):
    id: int
    title: str
    overview: str
    poster_path: Optional[str] = None
    popularity: float
    vote_count: int
    vote_average: float
    release_date: str
    popularity_score: float
    watched: Optional[bool] = None

# User rating models
class UserRatingRequest(BaseModel):
    clerk_user_id: str
    movie_id: int
    rating: float

class UserRatingResponse(BaseModel):
    id: int
    clerk_user_id: str
    movie_id: int
    rating: float
    created_at: str
    updated_at: str
    movie_title: Optional[str] = None
    movie_poster_path: Optional[str] = None
    movie_overview: Optional[str] = None
    movie_release_date: Optional[str] = None
    movie_original_language: Optional[str] = None
    movie_popularity: Optional[float] = None
    movie_vote_count: Optional[int] = None
    movie_vote_average: Optional[float] = None
    is_watchlisted: Optional[bool] = None

# Watchlist models
class WatchlistRequest(BaseModel):
    clerk_user_id: str
    movie_id: int

class WatchlistResponse(BaseModel):
    id: int
    clerk_user_id: str
    movie_id: int
    created_at: str
    movie_title: Optional[str] = None
    movie_poster_path: Optional[str] = None
    movie_overview: Optional[str] = None
    movie_release_date: Optional[str] = None
    movie_original_language: Optional[str] = None
    movie_popularity: Optional[float] = None
    movie_vote_count: Optional[int] = None
    movie_vote_average: Optional[float] = None

# Movie recommendations model
class MovieRecommendation(BaseModel):
    id: int
    title: str
    overview: str
    poster_path: Optional[str] = None
    release_date: str
    original_language: str
    popularity: float
    vote_count: int
    vote_average: float
    predicted_score: float
    predicted_star_rating: float
    user_rating: Optional[float] = None
    watched: bool

# User summary model
class UserSummary(BaseModel):
    user_id: str
    summary: str

# Preference recommendation model
class PreferenceRecommendation(BaseModel):
    title: str
    movies: List[MovieWithStats] 