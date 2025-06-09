from flask import Flask, request, jsonify
from app import fetch_json_with_selenium
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/fetch", methods=["GET"])
def fetch():
    try:
        url = request.args.get("url")
        logger.info(f"Received request for URL: {url}")
        
        if not url:
            logger.error("No URL provided in request")
            return jsonify({"error": "URL parameter is required"}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid URL format: {url}")
            return jsonify({"error": "URL must start with http:// or https://"}), 400
        
        logger.info(f"Attempting to fetch JSON from: {url}")
        success = fetch_json_with_selenium(url)
        
        if success:
            logger.info("Successfully fetched and saved JSON data")
            return jsonify({"status": "success", "message": "JSON data fetched and saved"})
        else:
            logger.error("Failed to fetch JSON data")
            return jsonify({"status": "failed", "message": "Failed to fetch JSON data"}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in fetch endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "JSON Fetcher"})

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    logger.info("Starting Flask application on port 3306")
    app.run(host="0.0.0.0", port=3306, debug=True)