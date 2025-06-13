from flask import Flask, request, render_template, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

# OpenWeatherMap API
API_KEY = "b835c11e8e4c9c7a3d03364563db2308"
BASE_URL = "http://api.openweathermap.org/data/2.5"

def get_weather_data(city_name):
    url = f"{BASE_URL}/weather?q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_weather_by_coords(lat, lon):
    url = f"{BASE_URL}/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_forecast_data(city_name):
    url = f"{BASE_URL}/forecast?q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_wind_direction(degrees):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return directions[round(degrees / 22.5) % 16]

def format_weather_data(data):
    if not data:
        return None

    sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
    sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')

    return {
        "city": data['name'],
        "country": data['sys']['country'],
        "temperature": round(data['main']['temp'], 1),
        "feels_like": round(data['main']['feels_like'], 1),
        "description": data['weather'][0]['description'],
        "icon": data['weather'][0]['icon'],
        "humidity": data['main']['humidity'],
        "pressure": data['main']['pressure'],
        "wind_speed": round(data['wind']['speed'] * 3.6, 1),
        "wind_direction": get_wind_direction(data['wind'].get('deg', 0)),
        "visibility": round(data.get('visibility', 0) / 1000, 1),
        "sunrise": sunrise,
        "sunset": sunset,
        "cloudiness": data['clouds']['all'],
        "temp_min": round(data['main']['temp_min'], 1),
        "temp_max": round(data['main']['temp_max'], 1),
        "last_updated": datetime.now().strftime('%H:%M'),
        "weather_type": data['weather'][0]['main'].lower(),  # for theme
        "timezone": data['timezone']
    }

def format_forecast_data(data):
    if not data:
        return []
    
    forecast_list = []
    for item in data['list'][:5]:
        forecast_list.append({
            "date": datetime.fromtimestamp(item['dt']).strftime('%a, %b %d'),
            "time": datetime.fromtimestamp(item['dt']).strftime('%H:%M'),
            "temperature": round(item['main']['temp'], 1),
            "description": item['weather'][0]['description'],
            "icon": item['weather'][0]['icon'],
            "humidity": item['main']['humidity'],
            "wind_speed": round(item['wind']['speed'] * 3.6, 1)
        })
    
    return forecast_list

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    forecast = None
    error_message = None

    city_name = request.form.get('city') if request.method == 'POST' else request.args.get('city')

    if city_name:
        weather_data = get_weather_data(city_name)
        if weather_data:
            weather = format_weather_data(weather_data)
            forecast_data = get_forecast_data(city_name)
            forecast = format_forecast_data(forecast_data)
        else:
            error_message = f"Weather data not found for '{city_name}'. Please try another city."

    weather_type = weather['weather_type'] if weather else None

    return render_template('index.html',
                           weather=weather,
                           forecast=forecast,
                           error_message=error_message,
                           weather_type=weather_type)

@app.route('/weather-by-coords')
def weather_by_coords():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude required"}), 400
    
    data = get_weather_by_coords(lat, lon)
    if data and data.get('name'):
        return jsonify({"city": data['name']})
    return jsonify({"error": "Could not fetch weather for coordinates"}), 500

@app.route('/api/weather/<city>')
def api_weather(city):
    data = get_weather_data(city)
    return jsonify(format_weather_data(data)) if data else jsonify({"error": "City not found"}), 404

@app.route('/api/forecast/<city>')
def api_forecast(city):
    data = get_forecast_data(city)
    return jsonify(format_forecast_data(data)) if data else jsonify({"error": "City not found"}), 404

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
