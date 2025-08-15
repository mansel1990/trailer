import mysql.connector
import os

# Database configuration
DB_CONFIG_SQL = {
    "host": "turntable.proxy.rlwy.net",
    "port": '25998',
    "user": "root",
    "password": "wKpjoSFmVkahchEZrgrqoPNGyuRvbXvl",
    "database": "trailer"
}

def create_cosine_similarity_function():
    """Create the cosine similarity function in MySQL"""
    conn = mysql.connector.connect(**DB_CONFIG_SQL)
    cursor = conn.cursor()
    
    try:
        # Read the SQL function from file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_cosine_similarity_function.sql')
        
        with open(sql_file_path, 'r') as file:
            sql_script = file.read()
        
        # Execute the function creation
        cursor.execute(sql_script)
        conn.commit()
        print("✅ Cosine similarity function created successfully")
        
    except mysql.connector.Error as e:
        if e.errno == 1304:  # Function already exists
            print("ℹ️ Cosine similarity function already exists")
        else:
            print(f"❌ Error creating function: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

def test_cosine_function():
    """Test the cosine similarity function"""
    conn = mysql.connector.connect(**DB_CONFIG_SQL)
    cursor = conn.cursor()
    
    try:
        # Test with simple vectors
        test_query = """
            SELECT COSINE_SIMILARITY(
                JSON_ARRAY(1, 2, 3), 
                JSON_ARRAY(1, 2, 3)
            ) as similarity
        """
        cursor.execute(test_query)
        result = cursor.fetchone()
        
        if result and result[0] == 1.0:
            print("✅ Cosine similarity function test passed")
        else:
            print(f"⚠️ Function test result: {result}")
            
    except Exception as e:
        print(f"❌ Error testing function: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to set up the cosine similarity function"""
    print("🎯 Setting up Cosine Similarity Function")
    print("=" * 40)
    
    # Create the function
    create_cosine_similarity_function()
    
    # Test the function
    test_cosine_function()
    
    print("🎉 Setup complete!")

if __name__ == "__main__":
    main() 