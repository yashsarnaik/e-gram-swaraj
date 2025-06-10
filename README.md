# URL Processing API

A FastAPI-based web service that processes URLs using Undetected ChromeDriver to extract content and JSON data from web pages.

## Features

- **Undetected ChromeDriver**: Uses undetected-chromedriver for better stealth and compatibility
- **Headed Browser Mode**: Runs in headed mode by default (as per user preference)
- **JSON Extraction**: Automatically detects and parses JSON content from web pages
- **RESTful API**: Clean FastAPI interface with automatic documentation
- **Error Handling**: Robust error handling and logging
- **Flexible Configuration**: Configurable wait times and timeouts

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome browser installed on your system.

## Usage

### Starting the API Server

#### Option 1: Using the startup script
```bash
python start_api.py
```

#### Option 2: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option 3: Running the main module
```bash
python main.py
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc

### API Endpoints

#### 1. Health Check
```
GET /health
```
Returns the health status of the API.

#### 2. Root Information
```
GET /
```
Returns basic information about the API and available endpoints.

#### 3. Process URL
```
POST /process-url
```

**Request Body:**
```json
{
    "url": "https://example.com/api/data",
    "wait_time": 3,
    "timeout": 30
}
```

**Parameters:**
- `url` (required): The URL to process
- `wait_time` (optional): Time to wait after page load in seconds (default: 3)
- `timeout` (optional): Page load timeout in seconds (default: 30)

**Response:**
```json
{
    "success": true,
    "url": "https://example.com/api/data",
    "content": "raw content from the page",
    "json_data": {"key": "value"},
    "content_type": "json",
    "status_code": 200,
    "error": null
}
```

### Example Usage with curl

```bash
# Health check
curl http://localhost:8000/health

# Process a JSON API
curl -X POST "http://localhost:8000/process-url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://jsonplaceholder.typicode.com/posts/1"}'

# Process with custom wait time
curl -X POST "http://localhost:8000/process-url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://httpbin.org/json", "wait_time": 5, "timeout": 60}'
```

### Example Usage with Python

```python
import requests

# Process a URL
response = requests.post(
    "http://localhost:8000/process-url",
    json={
        "url": "https://jsonplaceholder.typicode.com/posts/1",
        "wait_time": 3,
        "timeout": 30
    }
)

result = response.json()
if result["success"]:
    print("Content extracted successfully!")
    if result["json_data"]:
        print("JSON Data:", result["json_data"])
    else:
        print("Raw Content:", result["content"])
else:
    print("Error:", result["error"])
```

## Testing

Run the test suite to verify the API is working correctly:

```bash
python test_api.py
```

This will test all endpoints and try processing several different types of URLs.

## Legacy Script

The original `app.py` script is still available and can be used standalone:

```bash
python app.py
```

This will run the original interactive script that prompts for URLs and saves results to files.

## Configuration

### Browser Configuration

The API uses Undetected ChromeDriver with the following default settings:
- **Headed mode**: Browser window is visible (as per user preference)
- **No automation detection**: Uses undetected-chromedriver to avoid detection
- **Standard window size**: 1920x1080
- **Security options**: Disabled sandbox and dev-shm-usage for compatibility

### Logging

The application uses Python's built-in logging module. Logs include:
- Driver initialization status
- URL processing progress
- Error messages and stack traces
- Browser cleanup status

## Dependencies

See `requirements.txt` for the complete list of dependencies:
- FastAPI: Web framework
- Uvicorn: ASGI server
- Undetected ChromeDriver: Stealth browser automation
- Selenium: Web automation framework
- Pydantic: Data validation
- Additional supporting libraries

## Error Handling

The API includes comprehensive error handling:
- Invalid URLs return 400 Bad Request
- Server errors return 500 Internal Server Error
- Browser initialization failures are caught and reported
- All errors include descriptive messages

## Notes

- The browser runs in headed mode by default (visible window)
- Each request creates a new browser instance for isolation
- Browser instances are automatically cleaned up after each request
- The API is designed to handle various content types (JSON, HTML, plain text)
- Automatic JSON detection and parsing when possible
