import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://egramswaraj.gov.in/",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive"
}

response = requests.get("https://egramswaraj.gov.in/bankpendingavg.do", headers=headers)

with open("output.html", "w", encoding="utf-8") as f:
    f.write(response.text)
