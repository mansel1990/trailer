# Movie Recommendations API Examples

## Get Movie Recommendations

### All Recommendations
```bash
curl -X GET "http://localhost:8000/recommendations/1?limit=10" \
  -H "accept: application/json"
```

### Unwatched Movies Only
```bash
curl -X GET "http://localhost:8000/recommendations/1?watched=false&limit=10" \
  -H "accept: application/json"
```

### Watched Movies Only
```bash
curl -X GET "http://localhost:8000/recommendations/1?watched=true&limit=10" \
  -H "accept: application/json"
```

## Response Example
```json
[
  {
    "id": 899248,
    "title": "Movie Title",
    "overview": "Movie description...",
    "poster_path": "/poster.jpg",
    "release_date": "2023-01-01",
    "original_language": "en",
    "popularity": 15.5,
    "vote_count": 1000,
    "vote_average": 7.5,
    "predicted_score": 0.81256,
    "final_score": 456.25,
    "watched": false
  }
]
```

## Parameters

- `clerk_user_id` (path): User ID to get recommendations for
- `watched` (query, optional): Filter by watched status (true/false/null for all)
- `limit` (query, optional): Number of recommendations to return (default: 20)

## Scoring Algorithm

The recommendations are sorted by **final_score** which is calculated as:
```
final_score = predicted_score * 5 * popularity * vote_average
```

Where:
- `predicted_score`: The ML model's prediction (0-1)
- `popularity`: Movie's popularity score
- `vote_average`: Average user rating (0-10)

## Features

- **Personalized Recommendations**: Based on ML model predictions stored in `recommendations_movie` table
- **Watched Filter**: Option to filter by watched/unwatched status
- **Smart Scoring**: Combines predicted score with popularity and ratings
- **Rich Movie Data**: Returns complete movie information
- **Flexible Filtering**: Can get all, watched only, or unwatched only recommendations 