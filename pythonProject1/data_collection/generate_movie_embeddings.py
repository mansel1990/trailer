import mysql.connector
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import time

# Database configuration
DB_CONFIG_SQL = {
    "host": "turntable.proxy.rlwy.net",
    "port": '25998',
    "user": "root",
    "password": "wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl",
    "database": "trailer"
}

def create_embeddings_table():
    """Create the movie_embeddings table if it doesn't exist"""
    conn = mysql.connector.connect(**DB_CONFIG_SQL)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_embeddings (
                movie_id INT PRIMARY KEY,
                embedding JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("✅ movie_embeddings table created/verified")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    finally:
        cursor.close()
        conn.close()

def generate_movie_embeddings():
    """Generate embeddings for all movies and store them in the database"""
    # Load the embedding model
    print("🔄 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Connect to database
    conn = mysql.connector.connect(**DB_CONFIG_SQL)
    cursor = conn.cursor()
    
    try:
        # Get all movies with their overviews
        cursor.execute("""
            SELECT id, title, overview 
            FROM movies 
            WHERE overview IS NOT NULL AND overview != ''
        """)
        movies = cursor.fetchall()
        
        print(f"📽️ Found {len(movies)} movies to process")
        
        # Process movies in batches
        batch_size = 50
        processed = 0
        
        for i in tqdm(range(0, len(movies), batch_size), desc="Generating embeddings"):
            batch = movies[i:i + batch_size]
            
            for movie_id, title, overview in batch:
                try:
                    # Combine title and overview for better embedding
                    text = f"{title}: {overview}"
                    
                    # Generate embedding
                    embedding = model.encode(text)
                    
                    # Convert to JSON string for storage
                    embedding_json = json.dumps(embedding.tolist())
                    
                    # Insert or update embedding
                    cursor.execute("""
                        INSERT INTO movie_embeddings (movie_id, embedding)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE
                            embedding = VALUES(embedding),
                            updated_at = CURRENT_TIMESTAMP
                    """, (movie_id, embedding_json))
                    
                    processed += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing movie {movie_id}: {e}")
                    continue
            
            # Commit batch
            conn.commit()
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.1)
        
        print(f"✅ Successfully processed {processed} movies")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to run the embedding generation"""
    print("🎬 Movie Embeddings Generator")
    print("=" * 40)
    
    # Create table
    create_embeddings_table()
    
    # Generate embeddings
    generate_movie_embeddings()
    
    print("🎉 Embedding generation complete!")

if __name__ == "__main__":
    main() 