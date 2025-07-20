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

def get_connection():
    """Get a database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def execute_query(query, params=None):
    """Execute a query and return results"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

def execute_update(query, params=None):
    """Execute an update query and commit changes"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close() 