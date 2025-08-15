import requests
import mysql.connector
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DB_CONFIG_SQL = {
    "host": "turntable.proxy.rlwy.net",
    "port":'25998',
    "user": "root",
    "password": "wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl",
    "database": "trailer"
}
# -------------------------
# Config
# -------------------------
ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMWRjM2YxMTg4N2FjOGRjNjdmYzY1ZWY3M2ZiOWIwYSIsIm5iZiI6MTY2Mjg3NDc0Ny4xMiwic3ViIjoiNjMxZDc0N2JkYjhhMDAwMDdlZDFhNTAzIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.2Baz1-zRRhQTO8FKvanFxOpleZ-jDbM5jYX1AckkMss'
#


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
# Fetch all movie IDs from movies that need cast/crew update
# -------------------------
cur.execute("""
    SELECT DISTINCT m.id
    FROM movies m
    LEFT JOIN movie_cast mc ON m.id = mc.movie_id
    LEFT JOIN movie_crew mw ON m.id = mw.movie_id
    WHERE 
        (mc.movie_id IS NULL OR mw.movie_id IS NULL)
        OR (
            m.release_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
            OR m.release_date >= CURDATE()
        )
""")
movie_ids = [row[0] for row in cur.fetchall()]

print(f"Found {len(movie_ids)} movies to fetch or update cast & crew")

# -------------------------
# Fetch credits for each movie and insert into DB
# -------------------------
for movie_id in movie_ids:
    print(f"Fetching credits for movie_id: {movie_id}")
    url = f"{TMDB_BASE_URL}/{movie_id}/credits"

    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"  ⚠️ TMDb returned {response.status_code} for movie {movie_id}: {response.text}")
            time.sleep(2)
            continue

        data = response.json()
        cast_list = data.get("cast", [])
        crew_list = data.get("crew", [])

        # Insert cast
        for cast in cast_list:
            try:
                cur.execute("""
                    INSERT IGNORE INTO movie_cast (
                        movie_id, cast_id, name, character_role, order_in_cast, profile_path
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    movie_id,
                    cast.get("id"),
                    cast.get("name"),
                    cast.get("character"),
                    cast.get("order"),
                    cast.get("profile_path")
                ))
            except Exception as e:
                print(f"    ❌ Error inserting cast for movie {movie_id}: {e}")

        # Insert crew
        for crew in crew_list:
            try:
                cur.execute("""
                    INSERT IGNORE INTO movie_crew (
                        movie_id, crew_id, name, department, job, profile_path
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    movie_id,
                    crew.get("id"),
                    crew.get("name"),
                    crew.get("department"),
                    crew.get("job"),
                    crew.get("profile_path")
                ))
            except Exception as e:
                print(f"    ❌ Error inserting crew for movie {movie_id}: {e}")

        conn.commit() # avoid hammering TMDb

    except requests.exceptions.RequestException as e:
        print(f"  🔌 Request failed for movie {movie_id}: {e}")
        time.sleep(2)
        continue

# -------------------------
# Close DB
# -------------------------
cur.close()
conn.close()

print("✅ Done fetching and inserting cast & crew")