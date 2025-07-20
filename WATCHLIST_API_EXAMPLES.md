# Watchlist API Examples

## Add Movie to Watchlist

```bash
curl -X POST "http://localhost:8000/watchlist" \
  -H "Content-Type: application/json" \
  -d '{
    "clerk_user_id": "clerk_id_2",
    "movie_id": 123456
  }'
```

### Response
```json
{
  "message": "Watchlist update initiated",
  "clerk_user_id": "clerk_id_2",
  "movie_id": 123456,
  "status": "processing"
}
```

## Get User's Watchlist

```bash
curl -X GET "http://localhost:8000/watchlist/clerk_id_2" \
  -H "accept: application/json"
```

### Response
```json
[
  {
    "id": 1,
    "clerk_user_id": "clerk_id_2",
    "movie_id": 123456,
    "created_at": "2025-07-19 17:30:00",
    "movie_title": "Movie Title"
  }
]
```

## Remove from Watchlist

```bash
curl -X DELETE "http://localhost:8000/watchlist" \
  -H "Content-Type: application/json" \
  -d '{
    "clerk_user_id": "clerk_id_2",
    "movie_id": 123456
  }'
```

### Response
```json
{
  "message": "Watchlist removal initiated",
  "clerk_user_id": "clerk_id_2",
  "movie_id": 123456,
  "status": "processing"
}
```

## Features

- **Async Processing**: Watchlist updates happen in the background
- **Upsert**: Updates existing watchlist entries or creates new ones
- **Delete**: Removes movies from watchlist
- **Ordered Results**: Get watchlist ordered by added time (most recent first)
- **Movie Titles**: Includes movie titles in the response
- **Limit**: Returns maximum 40 items per request

## Database Schema

The watchlist table should have the following structure:
```sql
CREATE TABLE `watchlist` (
  `id` int NOT NULL AUTO_INCREMENT,
  `clerk_user_id` varchar(255) DEFAULT NULL,
  `movie_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_user_movie` (`clerk_user_id`,`movie_id`),
  KEY `idx_user` (`clerk_user_id`),
  KEY `idx_movie` (`movie_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
``` 