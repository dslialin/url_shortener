# URL Shortener

A FastAPI-based URL shortening service with Redis caching.

## Features

- Create short URLs
- Redirect to original URLs
- Get URL statistics
- Redis caching for better performance
- Search by original URL
- List all shortened URLs

## Requirements

- Python 3.8+
- Redis
- SQLite (included)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd url_shortener
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start Redis server (if not running)

5. Run the application:
```bash
uvicorn main:app --reload --port 8080
```

## API Endpoints

- `POST /links/shorten` - Create a new short URL
- `GET /{short_code}` - Redirect to original URL
- `GET /links/{short_code}/stats` - Get URL statistics
- `GET /links/search` - Search by original URL
- `GET /links` - List all shortened URLs

## Example Usage

Create a short URL:
```bash
curl -X POST "http://localhost:8080/links/shorten" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://www.example.com"}'
```

Get URL statistics:
```bash
curl "http://localhost:8080/links/{short_code}/stats"
```

## License

MIT 