# Localhost Proxy for JSON Fetcher

This application now includes a proxy server that makes web requests appear as if they're coming from a localhost computer.

## Features

- **Localhost Proxy Server**: Modifies HTTP headers to make requests appear local
- **Chrome Configuration**: Automatically configures Chrome to use the proxy
- **Header Modification**: Adds localhost-specific headers like `X-Forwarded-For: 127.0.0.1`
- **User Agent Spoofing**: Uses a Windows desktop user agent instead of mobile
- **Configurable**: Easy to enable/disable proxy functionality

## How It Works

1. **Proxy Server**: A simple HTTP proxy server (`proxy_server.py`) that:
   - Intercepts HTTP requests from Chrome
   - Modifies headers to appear as localhost (127.0.0.1)
   - Forwards requests to the target server
   - Returns responses back to Chrome

2. **Chrome Configuration**: Chrome is configured to:
   - Use the proxy server for all requests
   - Send localhost-like user agent
   - Include additional localhost headers

3. **Header Modifications**: The proxy adds/modifies these headers:
   - `X-Forwarded-For: 127.0.0.1`
   - `X-Real-IP: 127.0.0.1`
   - `X-Forwarded-Host: localhost`
   - `X-Forwarded-Proto: http`
   - `X-Forwarded-Port: 80`
   - `X-Original-Host: localhost`
   - `Remote-Addr: 127.0.0.1`
   - `Client-IP: 127.0.0.1`

## Usage

### Flask API

#### Basic fetch with proxy (default):
```
GET /fetch?url=https://example.com/api/data
```

#### Fetch without proxy:
```
GET /fetch?url=https://example.com/api/data&use_proxy=false
```

#### Custom proxy configuration:
```
GET /fetch?url=https://example.com/api/data&proxy_host=127.0.0.1&proxy_port=8888
```

#### Test proxy functionality:
```
GET /test-proxy?url=https://jsonplaceholder.typicode.com/posts/1
```

### Python Code

```python
from app import fetch_json_with_selenium

# With proxy (default)
fetch_json_with_selenium("https://example.com/api/data")

# Without proxy
fetch_json_with_selenium("https://example.com/api/data", use_proxy=False)

# Custom proxy settings
fetch_json_with_selenium(
    "https://example.com/api/data", 
    use_proxy=True, 
    proxy_host="127.0.0.1", 
    proxy_port=8888
)
```

## Configuration

Edit `config.py` to modify default settings:

```python
class Config:
    USE_PROXY_BY_DEFAULT = True  # Enable/disable proxy by default
    PROXY_HOST = "127.0.0.1"     # Proxy server host
    PROXY_PORT = 8888            # Proxy server port
    
    # Modify localhost headers
    LOCALHOST_HEADERS = {
        'X-Forwarded-For': '127.0.0.1',
        'X-Real-IP': '127.0.0.1',
        # ... more headers
    }
```

## Testing

Run the application and test both modes:

```bash
python app.py
```

This will test the same URL with and without the proxy, allowing you to compare the results.

## Docker

The proxy functionality works in Docker containers. The Dockerfile already includes all necessary dependencies.

## Troubleshooting

1. **Proxy not starting**: Check if port 8888 is available
2. **Chrome not using proxy**: Check Chrome logs for proxy configuration errors
3. **Headers not being modified**: Verify the proxy server is receiving requests
4. **Performance issues**: The proxy adds a small overhead to requests

## Security Notes

- The proxy server only runs locally (127.0.0.1)
- It's designed for development/testing purposes
- Headers are modified to appear as localhost, not to hide actual origin
- Use responsibly and in compliance with target website terms of service
