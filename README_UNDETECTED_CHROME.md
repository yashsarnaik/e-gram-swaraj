# Undetected ChromeDriver Integration

This project now supports **Undetected ChromeDriver** for more stealthy web automation that can bypass many anti-bot detection systems.

## What is Undetected ChromeDriver?

Undetected ChromeDriver is a modified version of Selenium's ChromeDriver that:
- Removes or modifies browser automation indicators
- Uses a real Chrome browser instead of Chromium
- Automatically handles Chrome version compatibility
- Bypasses many common bot detection mechanisms
- Provides better stealth capabilities for web scraping

## Installation

1. **Install the required dependency:**
   ```bash
   pip install undetected-chromedriver>=3.5.4
   ```

2. **Or install all dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.py` to control undetected ChromeDriver behavior:

```python
class Config:
    # Undetected ChromeDriver settings
    USE_UNDETECTED_CHROME = True  # Enable/disable undetected chrome
    UNDETECTED_CHROME_VERSION = None  # Auto-detect Chrome version
    UNDETECTED_CHROME_DRIVER_EXECUTABLE_PATH = None  # Auto-download driver
    
    # Chrome settings (applies to both regular and undetected)
    CHROME_HEADLESS = False  # Set to True for headless mode
    CHROME_WINDOW_SIZE = "1920,1080"
```

### Configuration Options:

- **`USE_UNDETECTED_CHROME`**: Set to `True` to use undetected ChromeDriver, `False` for regular ChromeDriver
- **`UNDETECTED_CHROME_VERSION`**: Specify Chrome version (e.g., `120`) or `None` for auto-detection
- **`UNDETECTED_CHROME_DRIVER_EXECUTABLE_PATH`**: Path to ChromeDriver executable or `None` for auto-download
- **`CHROME_HEADLESS`**: Run browser in headless mode (recommended: `False` for better stealth)

## Usage

The integration is seamless - your existing code will automatically use undetected ChromeDriver when enabled:

### Python Code:
```python
from app import fetch_json_with_selenium

# This will now use undetected ChromeDriver if enabled in config
result = fetch_json_with_selenium("https://example.com/api/data")
```

### Flask API:
```bash
# Same endpoints work with undetected ChromeDriver
GET /fetch?url=https://example.com/api/data
```

## Testing

Run the test script to verify the integration:

```bash
python test_undetected_chrome.py
```

This will:
- Test basic functionality with undetected ChromeDriver
- Compare regular vs undetected ChromeDriver
- Generate output files for inspection
- Show detailed logs of the process

## Comparison: Regular vs Undetected ChromeDriver

| Feature | Regular ChromeDriver | Undetected ChromeDriver |
|---------|---------------------|------------------------|
| Bot Detection | Easily detected | Much harder to detect |
| Browser Type | Chromium | Real Chrome |
| Automation Flags | Visible | Hidden/Modified |
| Version Management | Manual | Automatic |
| Stealth Level | Low | High |
| Performance | Fast | Slightly slower |

## Benefits of Undetected ChromeDriver

1. **Better Success Rate**: Higher success rate on websites with anti-bot protection
2. **Automatic Updates**: Automatically handles Chrome version compatibility
3. **Stealth Features**: Removes automation indicators that websites check for
4. **Real Browser**: Uses actual Chrome instead of Chromium
5. **Easy Integration**: Drop-in replacement for regular ChromeDriver

## Troubleshooting

### Common Issues:

1. **Chrome Version Mismatch**:
   - Solution: Set `UNDETECTED_CHROME_VERSION = None` for auto-detection
   - Or specify your Chrome version manually

2. **Driver Download Issues**:
   - Solution: Ensure internet connection for auto-download
   - Or manually specify driver path

3. **Headless Mode Detection**:
   - Solution: Set `CHROME_HEADLESS = False` for better stealth
   - Some sites can detect headless browsers

4. **Proxy Issues**:
   - Solution: Test without proxy first
   - Some proxy configurations may interfere with stealth features

### Debug Mode:

Enable debug logging in your script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Use Headed Mode**: Set `CHROME_HEADLESS = False` for maximum stealth
2. **Reasonable Delays**: Add delays between requests to avoid rate limiting
3. **Rotate User Agents**: Though undetected chrome handles this automatically
4. **Monitor Success Rates**: Test regularly to ensure continued effectiveness
5. **Fallback Strategy**: Keep regular ChromeDriver as backup option

## Switching Between Drivers

You can easily switch between regular and undetected ChromeDriver:

```python
from config import Config

# Use undetected ChromeDriver
Config.USE_UNDETECTED_CHROME = True

# Use regular ChromeDriver
Config.USE_UNDETECTED_CHROME = False
```

## Performance Considerations

- Undetected ChromeDriver may be slightly slower due to additional stealth measures
- First run may take longer due to Chrome/driver downloads
- Subsequent runs are faster as components are cached
- Headed mode uses more resources but provides better stealth

## Security Notes

- Undetected ChromeDriver downloads Chrome and ChromeDriver automatically
- Ensure you trust the source and have proper network security
- Consider using in isolated environments for sensitive operations
- Regular updates are recommended for security and compatibility
