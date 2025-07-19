from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector
import os

#mansel94..root

DB_CONFIG_SQL = {
    "host": "turntable.proxy.rlwy.net",
    "port":'25998',
    "user": "root",
    "password": "wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl",
    "database": "trailer"
}

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
'''
@app.get("/recommendations/{user_id}")
def recommend(user_id: int, top_n: int = 5):
    recs = get_top_recommendations(user_id, top_n)
    if recs.empty:
        return {"message": "No recommendations found."}

    rated_df = get_user_rated_data(user_id, model)
    rated_df = cluster_user_tastes(rated_df)

    output = []
    for _, rec_row in recs.iterrows():
        if len(rated_df) > 100:
            why = gpt_explain(user_id, rec_row)  # optional fallback
        else:
            why = rag_explanation_auto(user_id, rec_row, rated_df, model)

        output.append({
            "movie_id": rec_row["movie_id"],
            "title": rec_row["title"],
            "predicted_score": rec_row["predicted_score"],
            "why_recommended": why
        })

    return {"user_id": user_id, "recommendations": output}'''