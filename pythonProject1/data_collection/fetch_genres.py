import json

import requests
import mysql.connector
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pythonProject1.config_sql import DB_CONFIG_SQL

# -------------------------
# Config
# -------------------------
ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMWRjM2YxMTg4N2FjOGRjNjdmYzY1ZWY3M2ZiOWIwYSIsIm5iZiI6MTY2Mjg3NDc0Ny4xMiwic3ViIjoiNjMxZDc0N2JkYjhhMDAwMDdlZDFhNTAzIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.2Baz1-zRRhQTO8FKvanFxOpleZ-jDbM5jYX1AckkMss'

TMDB_BASE_URL = "https://api.themoviedb.org/3/movie"
HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer " + ACCESS_TOKEN
}

# -------------------------
# TMDb resilient session
# -------------------------
def get_tmdb_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session

session = get_tmdb_session()

# -------------------------
# DB connection
# -------------------------
conn = mysql.connector.connect(**DB_CONFIG_SQL)
cur = conn.cursor(buffered=True)

# -------------------------
# Fetch all movie IDs and titles from movies
# -------------------------
cur.execute("SELECT id, title FROM movies")
movies = cur.fetchall()

print(f"Found {len(movies)} movies to fetch genres")

# -------------------------
# Create genres table if not exists
# -------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS tmdb_movie_genres (
    movie_id INT PRIMARY KEY,
    title TEXT,
    tmdb_genres TEXT
)
""")
conn.commit()

# -------------------------
# Fetch genres for each movie and upsert into DB
# -------------------------
for movie_id, title in movies:
    print(f"Fetching genres for movie_id: {movie_id}")

    url = f"{TMDB_BASE_URL}/{movie_id}"

    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            genres = [genre["name"].lower() for genre in data.get("genres", [])]
            genres_json = json.dumps(genres)

            try:
                cur.execute("""
                    INSERT INTO tmdb_movie_genres (movie_id, title, tmdb_genres)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        tmdb_genres = VALUES(tmdb_genres)
                """, (movie_id, title, genres_json))
                conn.commit()
            except Exception as e:
                print(f"    ❌ DB insert error for movie {movie_id}: {e}")

        else:
            print(f"  ⚠️ TMDb returned {response.status_code} for movie {movie_id}: {response.text}")
            # Backoff on 429 or server errors
            if response.status_code in (429, 500, 502, 503, 504):
                wait_time = int(response.headers.get("Retry-After", 5))
                print(f"  Sleeping for {wait_time} seconds due to rate limiting or server error")
                time.sleep(wait_time)
            else:
                time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"  🔌 Request failed for movie {movie_id}: {e}")
        time.sleep(5)
        continue

    time.sleep(0.5)  # rate limit buffer

# -------------------------
# Close DB
# -------------------------
cur.close()
conn.close()

print("✅ Done fetching and inserting TMDB genres")
