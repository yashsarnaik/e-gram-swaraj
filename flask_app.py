from flask import Flask, request
from app import fetch_json_with_selenium

app = Flask(__name__)

@app.route("/fetch", methods=["GET"])
def fetch():
    url = request.args.get("url")
    if not url:
        return "URL missing", 400
    success = fetch_json_with_selenium(url)
    return ("Success" if success else "Failed")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3306)
