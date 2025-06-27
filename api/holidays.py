import requests
from bs4 import BeautifulSoup
import time
import socket
from datetime import datetime
import random

# Simplified user-agent list (since user_agent_generator won't work on Vercel)
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X)"
]

def handler(request, response):
    if request.method == "OPTIONS":
        return response.json({}, status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })

    # Get ?year= from query, fallback to current year
    year = request.query.get("year") or datetime.now().year
    try:
        year = int(year)
    except ValueError:
        year = datetime.now().year

    start_time = time.time()
    url = f'https://www.officialgazette.gov.ph/nationwide-holidays/{year}/'
    domain = url.split("//")[-1].split("/")[0]

    try:
        ip_address = socket.gethostbyname(domain)
    except socket.gaierror:
        return response.json({'error': 'Failed to resolve domain name'}, status=500, headers=cors_headers())

    headers = {
        'User-Agent': random.choice(user_agents)
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        return response.json({'error': f'Failed to fetch: {str(e)}'}, status=500, headers=cors_headers())

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
        return response.json({'error': f'HTML parse error: {e}'}, status=500, headers=cors_headers())

    return response.json({
        'request_timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        'response_duration_seconds': round(time.time() - start_time, 2),
        'source_url': url,
        'source_ip': ip_address,
        'number_of_holidays': len(holidays),
        'holidays': holidays
    }, headers=cors_headers())

# CORS headers
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }
