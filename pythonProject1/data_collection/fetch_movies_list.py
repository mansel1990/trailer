import time

import requests
import mysql.connector
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from pythonProject1.config_sql import DB_CONFIG_SQL

ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMWRjM2YxMTg4N2FjOGRjNjdmYzY1ZWY3M2ZiOWIwYSIsIm5iZiI6MTY2Mjg3NDc0Ny4xMiwic3ViIjoiNjMxZDc0N2JkYjhhMDAwMDdlZDFhNTAzIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.2Baz1-zRRhQTO8FKvanFxOpleZ-jDbM5jYX1AckkMss'
# TMDb API setup
# API setup

BASE_URL = "https://api.themoviedb.org/3/discover/movie"
HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer " + ACCESS_TOKEN
}

LANGUAGES = {
    'ta': 'Tamil',
    'hi': 'Hindi',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'te': 'Telugu',
    'en': 'English'
}

PAGES_PER_LANGUAGE = 100  # ~2000 movies per language × 6 = ~12,000 total
DELAY_BETWEEN_REQUESTS = 0.5

# -------------------------
# 🔁 TMDb Resilient Session
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
# 🧩 MYSQL CONNECT
# -------------------------

conn = mysql.connector.connect(**DB_CONFIG_SQL)
cur = conn.cursor()

movies_inserted = 0

# -------------------------
# 🔄 Fetch & Insert
# -------------------------

for lang_code, lang_name in LANGUAGES.items():
    print(f"\n🌍 Fetching movies in {lang_name} ({lang_code})")

    for page in range(1, PAGES_PER_LANGUAGE + 1):
        print(f"  🔄 Page {page} for {lang_name}")

        params = {
            "include_adult": False,
            "include_video": False,
            "language": "en-US",  # Response in English
            "with_original_language": lang_code,
            "sort_by": "popularity.desc",
            "page": page
        }

        try:
            response = session.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
            if response.status_code != 200:
                print(f"    ❌ TMDb Error {response.status_code}: {response.text}")
                time.sleep(2)
                continue

            data = response.json()
            movies = data.get("results", [])
            if not movies:
                print("    🚫 No more movies")
                break

            for m in movies:
                try:
                    cur.execute("""
                        INSERT IGNORE INTO movies(
                            id, title, original_title, original_language, overview,
                            release_date, popularity, vote_average, vote_count, video, poster_path
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        m["id"],
                        m.get("title", ""),
                        m.get("original_title", ""),
                        m.get("original_language", ""),
                        m.get("overview", ""),
                        m.get("release_date", None),
                        m.get("popularity", 0.0),
                        m.get("vote_average", 0.0),
                        m.get("vote_count", 0),
                        m.get("video", False),
                        m.get("poster_path", "")
                    ))
                    movies_inserted += 1
                except Exception as db_error:
                    print(f"    ⚠️ MySQL insert failed for movie ID {m.get('id')}: {db_error}")

            conn.commit()
            time.sleep(DELAY_BETWEEN_REQUESTS)

        except requests.exceptions.RequestException as req_error:
            print(f"    🔌 Request failed on page {page} of {lang_name}: {req_error}")
            time.sleep(2)
            continue

print(f"\n✅ Done. Total movies inserted: {movies_inserted}")

# -------------------------
# 🔒 Close DB
# -------------------------

cur.close()
conn.close()