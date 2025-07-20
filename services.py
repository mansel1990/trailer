import asyncio
from database import execute_update, execute_query

async def update_user_rating_async(clerk_user_id: str, movie_id: int, rating: float):
    """Async function to update user rating in the background"""
    try:
        print(f"Background: Starting rating update for user {clerk_user_id}, movie {movie_id}, rating {rating}")
        
        # Check if rating is valid (0-5 in 0.5 steps)
        if rating < 0 or rating > 5 or (rating * 10) % 5 != 0:
            raise ValueError("Rating must be between 0 and 5 in 0.5 steps")
        
        # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert
        query = """
            INSERT INTO user_ratings (clerk_user_id, movie_id, rating, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE 
                rating = VALUES(rating),
                updated_at = CURRENT_TIMESTAMP
        """
        
        execute_update(query, (clerk_user_id, movie_id, rating))
        print(f"Background: Successfully updated rating for user {clerk_user_id}, movie {movie_id} to {rating}")
        
    except Exception as e:
        print(f"Background: Error updating rating: {str(e)}")
        print(f"Background: Error type: {type(e)}")

async def add_to_watchlist_async(clerk_user_id: str, movie_id: int):
    """Async function to add movie to watchlist in the background"""
    try:
        print(f"Background: Starting watchlist update for user {clerk_user_id}, movie {movie_id}")
        
        # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert
        query = """
            INSERT INTO watchlist (clerk_user_id, movie_id, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE 
                created_at = CURRENT_TIMESTAMP
        """
        
        execute_update(query, (clerk_user_id, movie_id))
        print(f"Background: Successfully added movie {movie_id} to watchlist for user {clerk_user_id}")
        
    except Exception as e:
        print(f"Background: Error adding to watchlist: {str(e)}")
        print(f"Background: Error type: {type(e)}")

async def remove_from_watchlist_async(clerk_user_id: str, movie_id: int):
    """Async function to remove movie from watchlist in the background"""
    try:
        print(f"Background: Starting watchlist removal for user {clerk_user_id}, movie {movie_id}")
        
        # Delete the watchlist entry
        query = """
            DELETE FROM watchlist 
            WHERE clerk_user_id = %s AND movie_id = %s
        """
        
        deleted_rows = execute_update(query, (clerk_user_id, movie_id))
        
        if deleted_rows > 0:
            print(f"Background: Successfully removed movie {movie_id} from watchlist for user {clerk_user_id}")
        else:
            print(f"Background: No movie {movie_id} found in watchlist for user {clerk_user_id}")
        
    except Exception as e:
        print(f"Background: Error removing from watchlist: {str(e)}")
        print(f"Background: Error type: {type(e)}") 