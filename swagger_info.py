#!/usr/bin/env python3
"""
Information about accessing Swagger documentation for the Movie API
"""

def print_swagger_info():
    print("🎬 Movie Trailer API - Swagger Documentation")
    print("=" * 50)
    
    print("\n📖 How to Access Swagger Documentation:")
    print("1. Start the server: python main.py")
    print("2. Open your browser and go to: http://localhost:8000/docs")
    print("3. Alternative: http://localhost:8000/redoc (ReDoc format)")
    
    print("\n🔧 API Endpoints Available:")
    print("• Basic Endpoints:")
    print("  - GET / - Root endpoint")
    print("  - GET /health - Health check")
    
    print("\n• Movie Endpoints:")
    print("  - GET /movies - Popular Tamil movies")
    print("  - GET /movies/popular/recent - Recent popular movies")
    print("  - GET /movies/upcoming - Upcoming movies")
    
    print("\n• Rating Endpoints:")
    print("  - POST /ratings - Add/update user rating")
    print("  - GET /ratings/{clerk_user_id} - Get user ratings")
    
    print("\n• Watchlist Endpoints:")
    print("  - POST /watchlist - Add to watchlist")
    print("  - GET /watchlist/{clerk_user_id} - Get user watchlist")
    print("  - DELETE /remove-from-watchlist - Remove from watchlist")
    
    print("\n• Recommendation Endpoints:")
    print("  - GET /recommendations/{clerk_user_id} - Get movie recommendations")
    
    print("\n• Debug Endpoints:")
    print("  - GET /debug/ratings-table - Debug ratings table")
    print("  - GET /debug/watchlist-table - Debug watchlist table")
    
    print("\n✨ Swagger Features:")
    print("• Interactive API documentation")
    print("• Try-it-out functionality")
    print("• Request/response examples")
    print("• Parameter validation")
    print("• Error response documentation")
    print("• Detailed endpoint descriptions")
    
    print("\n🚀 Quick Start:")
    print("1. Run: python main.py")
    print("2. Visit: http://localhost:8000/docs")
    print("3. Click 'Try it out' on any endpoint")
    print("4. Fill in parameters and execute")
    
    print("\n📝 Example Usage:")
    print("• Test health: GET /health")
    print("• Get movies: GET /movies")
    print("• Get recommendations: GET /recommendations/1?limit=5")
    print("• Add rating: POST /ratings with JSON body")

if __name__ == "__main__":
    print_swagger_info() 