from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import time
import socket
from datetime import datetime
import random

app = Flask(__name__)

# Simplified user-agent list (since user_agent_generator won't work on Vercel)
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X)"
]

@app.route('/', methods=['GET'])
@app.route('/holidays', methods=['GET'])
@app.route('/holidays/<int:year>', methods=['GET'])
def get_holidays(year=None):
    # Get year from query param or path or default to current year
    if year is None:
        year = request.args.get('year', default=datetime.now().year, type=int)
    start_time = time.time()
    url = f'https://www.officialgazette.gov.ph/nationwide-holidays/{year}/'
    domain = url.split("//")[-1].split("/")[0]

    try:
        ip_address = socket.gethostbyname(domain)
    except socket.gaierror:
        return jsonify({'error': 'Failed to resolve domain name'}), 500

    headers = {
        'User-Agent': random.choice(user_agents)
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch: {str(e)}'}), 500

    try:
        soup = BeautifulSoup(res.content, 'html.parser')
        holidays = []

        tables = soup.find_all("table")
        for i, table in enumerate(tables):
            holiday_type = "Regular Holidays" if i == 0 else "Special (Non-Working) Holidays"
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    event = cols[0].get_text(strip=True)
                    date = cols[1].get_text(strip=True)
                    holidays.append({'event': event, 'date': date, 'type': holiday_type})
    except Exception as e:
        return jsonify({'error': f'HTML parse error: {e}'}), 500

    return jsonify({
        'request_timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        'response_duration_seconds': round(time.time() - start_time, 2),
        'source_url': url,
        'source_ip': ip_address,
        'number_of_holidays': len(holidays),
        'holidays': holidays
    })

# CORS headers
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

# Do not call app.run() here; Vercel will handle running the app
