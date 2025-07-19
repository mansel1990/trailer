from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector
import os

# Database configuration from environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "turntable.proxy.rlwy.net"),
    "port": int(os.getenv("DB_PORT", "25998")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl"),
    "database": os.getenv("DB_NAME", "trailer")
}

app = FastAPI(
    title="Movie Trailer API",
    description="API for movie recommendations and data",
    version="1.0.0"
)

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model
class Movie(BaseModel):
    id: int
    title: str
    overview: str
    poster_path: str

@app.get("/")
def read_root():
    return {"message": "Movie Trailer API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/movies", response_model=List[Movie])
def get_movies():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, overview, poster_path FROM movies "
                       " where original_language='ta' and release_date<CURRENT_TIMESTAMP()"
                       " order by popularity desc "
                       "limit 40")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
        movie = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if movie:
            return movie
        else:
            return {"error": "Movie not found"}
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 