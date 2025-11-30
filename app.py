import os
import requests
from flask import Flask, render_template, request, jsonify

# Create Flask app
app = Flask(__name__)

# Open-Meteo API base URL (no API key required)
BASE_URL = 'https://api.open-meteo.com/v1/forecast'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form.get('city')
    
    if not city:
        return render_template('index.html', error='City name is required')
    
    try:
        # First, we need to get the coordinates for the city using Open-Meteo's geocoding API
        geocode_url = 'https://geocoding-api.open-meteo.com/v1/search'
        geocode_params = {
            'name': city,
            'count': 1
        }
        
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_data = geocode_response.json()
        
        if not geocode_data.get('results'):
            return render_template('index.html', error=f'City "{city}" not found')
        
        # Get coordinates from geocoding response
        latitude = geocode_data['results'][0]['latitude']
        longitude = geocode_data['results'][0]['longitude']
        country = geocode_data['results'][0].get('country', '')
        
        # Now get weather data using coordinates
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current_weather': True,
            'temperature_unit': 'celsius'
        }
        
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if response.status_code == 200:
            current_weather = data['current_weather']
            weather_data = {
                'city': city,
                'country': country,
                'temperature': current_weather['temperature'],
                'description': describe_weather(current_weather['weathercode']),
                'humidity': 'N/A',  # Not provided in free tier
                'pressure': 'N/A',  # Not provided in free tier
                'wind_speed': current_weather['windspeed'],
                'icon': get_weather_icon(current_weather['weathercode'])
            }
            return render_template('index.html', weather=weather_data)
        else:
            error_message = 'Error fetching weather data'
            return render_template('index.html', error=error_message)
            
    except Exception as e:
        return render_template('index.html', error='An error occurred while fetching weather data')

# Helper functions for weather description and icons
def describe_weather(weather_code):
    weather_descriptions = {
        0: 'Clear sky',
        1: 'Mainly clear',
        2: 'Partly cloudy',
        3: 'Overcast',
        45: 'Fog',
        48: 'Depositing rime fog',
        51: 'Light drizzle',
        53: 'Moderate drizzle',
        55: 'Dense drizzle',
        61: 'Slight rain',
        63: 'Moderate rain',
        65: 'Heavy rain',
        71: 'Slight snow fall',
        73: 'Moderate snow fall',
        75: 'Heavy snow fall',
        95: 'Thunderstorm',
        96: 'Thunderstorm with slight hail',
        99: 'Thunderstorm with heavy hail'
    }
    return weather_descriptions.get(weather_code, 'Unknown')

def get_weather_icon(weather_code):
    # Simplified icon mapping
    if weather_code == 0:
        return '01d'  # Clear sky
    elif weather_code in [1, 2]:
        return '02d'  # Few clouds
    elif weather_code in [3, 45, 48]:
        return '03d'  # Scattered clouds / fog
    elif weather_code in [51, 53, 55, 61, 63, 65]:
        return '09d'  # Rain
    elif weather_code in [71, 73, 75]:
        return '13d'  # Snow
    elif weather_code in [95, 96, 99]:
        return '11d'  # Thunderstorm
    else:
        return '03d'  # Default

# Make sure app is accessible as a module-level variable for gunicorn
application = app

if __name__ == '__main__':
    # Use Railway's PORT environment variable, default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    # Listen on all addresses for Railway
    app.run(host='0.0.0.0', port=port, debug=False)
