from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector
import os

from config_sql import DB_CONFIG_SQL

app = FastAPI()

# CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_CONFIG = {
    **DB_CONFIG_SQL
}

# Pydantic model
class Movie(BaseModel):
    id: int
    title: str
    overview: str
    poster_path: str

@app.get("/movies", response_model=List[Movie])
def get_movies():
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