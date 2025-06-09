"""
Configuration settings for the JSON fetcher with proxy support
"""

import os

class Config:
    # Proxy settings
    USE_PROXY_BY_DEFAULT = True
    PROXY_HOST = "127.0.0.1"
    PROXY_PORT = 8888
    
    # Chrome settings
    CHROME_HEADLESS = True
    CHROME_WINDOW_SIZE = "1920,1080"
    
    # Localhost headers to add
    LOCALHOST_HEADERS = {
        'X-Forwarded-For': '127.0.0.1',
        'X-Real-IP': '127.0.0.1',
        'X-Forwarded-Host': 'localhost',
        'X-Forwarded-Proto': 'http',
        'X-Forwarded-Port': '80',
        'X-Original-Host': 'localhost',
        'Remote-Addr': '127.0.0.1',
        'Client-IP': '127.0.0.1'
    }
    
    # User agent for localhost appearance
    LOCALHOST_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Flask settings
    FLASK_HOST = "0.0.0.0"
    FLASK_PORT = 3306
    FLASK_DEBUG = True
    
    # Logging
    LOG_LEVEL = "DEBUG"
    
    @classmethod
    def get_proxy_config(cls):
        """Get proxy configuration"""
        return {
            'use_proxy': cls.USE_PROXY_BY_DEFAULT,
            'host': cls.PROXY_HOST,
            'port': cls.PROXY_PORT
        }
    
    @classmethod
    def get_chrome_options_args(cls):
        """Get Chrome options arguments"""
        args = [
            "--headless" if cls.CHROME_HEADLESS else "",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            f"--window-size={cls.CHROME_WINDOW_SIZE}",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",
            "--disable-javascript",
            f"--user-agent={cls.LOCALHOST_USER_AGENT}",
            "--disable-software-rasterizer",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding"
        ]
        return [arg for arg in args if arg]  # Filter out empty strings
    
    @classmethod
    def get_localhost_header_args(cls):
        """Get Chrome arguments for localhost headers"""
        header_args = []
        for key, value in cls.LOCALHOST_HEADERS.items():
            header_args.append(f"--add-header={key}:{value}")
        return header_args
