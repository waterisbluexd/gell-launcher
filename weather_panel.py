#!/usr/bin/env python3
"""Weather panel for Gell Launcher."""

import subprocess
import json
from datetime import datetime
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container, Horizontal, Vertical

class WeatherPanel(Container):
    """A panel displaying current weather with ASCII art and forecast."""
    DEFAULT_CLASSES = "panel-weather"

    # ASCII art for different weather conditions
    WEATHER_ART = {
        'clear': [
            "    \\   /    ",
            "     .-.     ",
            "  ― (   ) ―  ",
            "     `-'     ",
            "    /   \\    "
        ],
        'partly_cloudy': [
            "   \\  /      ",
            " _ /\"\".-.    ",
            "   \\_(   ).  ",
            "   /(___(__) ",
            "             "
        ],
        'cloudy': [
            "             ",
            "     .--.    ",
            "  .-(    ).  ",
            " (___.__)__) ",
            "             "
        ],
        'rain': [
            "     .-.     ",
            "    (   ).   ",
            "   (___(__)  ",
            "    ʻ‚ʻ‚ʻ‚   ",
            "    ‚ʻ‚ʻ‚    "
        ],
        'heavy_rain': [
            "     .-.     ",
            "    (   ).   ",
            "   (___(__)  ",
            "  ‚ʻ‚ʻ‚ʻ‚ʻ   ",
            "  ‚ʻ‚ʻ‚ʻ‚ʻ   "
        ],
        'thunderstorm': [
            "     .-.     ",
            "    (   ).   ",
            "   (___(__)  ",
            "   ⚡ ʻ‚ʻ‚    ",
            "    ʻ‚⚡ʻ     "
        ],
        'snow': [
            "     .-.     ",
            "    (   ).   ",
            "   (___(__)  ",
            "    * * * *  ",
            "   * * * *   "
        ],
        'mist': [
            "             ",
            " _ - _ - _ - ",
            "  _ - _ - _  ",
            " _ - _ - _ - ",
            "             "
        ],
        'default': [
            "     .-.     ",
            "    (   ).   ",
            "   (___(__)  ",
            "             ",
            "             "
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_timer = None
        self.weather_data = None
        self.last_update = None

    def compose(self) -> ComposeResult:
        """Compose the weather panel widgets."""
        # Top section - split into left (art) and right (info)
        with Container(id="weather-top-section"):
            with Horizontal(id="weather-top-inner"):
                # Left side - ASCII art
                yield Static("Loading...", id="weather-art", classes="weather-art")
                
                # Right side - weather info
                with Vertical(id="weather-info-section"):
                    yield Static("Good Morning", id="weather-greeting", classes="weather-greeting")
                    yield Static("Sunny", id="weather-condition", classes="weather-condition")
                    yield Static("15°C", id="weather-temp", classes="weather-temp-main")
                    yield Static("Wind: 10 km/h", id="weather-wind", classes="weather-info-detail")
                    yield Static("Humidity: 65%", id="weather-humidity", classes="weather-info-detail")
        
        # Bottom section - hourly forecast
        yield Static("Loading forecast...", id="weather-hourly", classes="weather-hourly")

    def on_mount(self) -> None:
        """Start the timer to refresh weather when the widget is mounted."""
        self.update_weather()
        # Update every 10 minutes (600 seconds)
        self.update_timer = self.set_interval(600.0, self.update_weather)

    def on_unmount(self) -> None:
        """Stop the timer when the widget is unmounted."""
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

    def get_greeting(self) -> str:
        """Get time-based greeting."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good Morning"
        elif 12 <= hour < 17:
            return "Good Afternoon"
        elif 17 <= hour < 21:
            return "Good Evening"
        else:
            return "Good Night"

    def get_weather_art(self, condition: str) -> str:
        """Get ASCII art based on weather condition."""
        condition_lower = condition.lower()
        
        # Map weather conditions to art
        if 'clear' in condition_lower or 'sunny' in condition_lower:
            art = self.WEATHER_ART['clear']
        elif 'partly' in condition_lower or 'partial' in condition_lower:
            art = self.WEATHER_ART['partly_cloudy']
        elif 'cloud' in condition_lower or 'overcast' in condition_lower:
            art = self.WEATHER_ART['cloudy']
        elif 'thunder' in condition_lower or 'storm' in condition_lower:
            art = self.WEATHER_ART['thunderstorm']
        elif 'heavy rain' in condition_lower or 'pouring' in condition_lower:
            art = self.WEATHER_ART['heavy_rain']
        elif 'rain' in condition_lower or 'drizzle' in condition_lower or 'shower' in condition_lower:
            art = self.WEATHER_ART['rain']
        elif 'snow' in condition_lower or 'sleet' in condition_lower:
            art = self.WEATHER_ART['snow']
        elif 'mist' in condition_lower or 'fog' in condition_lower or 'haze' in condition_lower:
            art = self.WEATHER_ART['mist']
        else:
            art = self.WEATHER_ART['default']
        
        return "\n".join(art)

    def fetch_weather_data(self) -> dict:
        """Fetch weather data using wttr.in API."""
        try:
            # Use wttr.in API with JSON format
            result = subprocess.run(
                ['curl', '-s', 'wttr.in/?format=j1'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                current = data.get('current_condition', [{}])[0]
                weather = data.get('weather', [{}])[0]
                hourly = weather.get('hourly', [])
                
                return {
                    'temp': current.get('temp_C', 'N/A'),
                    'feels_like': current.get('FeelsLikeC', 'N/A'),
                    'condition': current.get('weatherDesc', [{}])[0].get('value', 'Unknown'),
                    'humidity': current.get('humidity', 'N/A'),
                    'wind_speed': current.get('windspeedKmph', 'N/A'),
                    'wind_dir': current.get('winddir16Point', 'N/A'),
                    'precipitation': current.get('precipMM', 'N/A'),
                    'hourly': hourly[:6]  # Get next 6 time slots
                }
        except Exception as e:
            pass
        
        return None

    def format_hourly_forecast(self, hourly_data: list) -> str:
        """Format hourly forecast data."""
        if not hourly_data:
            return "No forecast data available"
        
        lines = []
        
        # Time row
        times = []
        for hour in hourly_data:
            time_str = hour.get('time', '0000')
            # Convert military time to readable format
            hour_num = int(time_str) // 100
            if hour_num == 0:
                times.append("12am")
            elif hour_num < 12:
                times.append(f"{hour_num}am")
            elif hour_num == 12:
                times.append("12pm")
            else:
                times.append(f"{hour_num-12}pm")
        
        lines.append("  ".join(f"{t:>5}" for t in times))
        
        # Temperature row
        temps = [f"{h.get('tempC', 'N/A')}°C" for h in hourly_data]
        lines.append("  ".join(f"{t:>5}" for t in temps))
        
        # Wind row
        winds = [f"{h.get('windspeedKmph', 'N/A')}km/h" for h in hourly_data]
        lines.append("  ".join(f"{w:>5}" for w in winds))
        
        # Humidity row
        humidities = [f"{h.get('humidity', 'N/A')}%" for h in hourly_data]
        lines.append("  ".join(f"{hum:>5}" for hum in humidities))
        
        return "\n".join(lines)

    def update_weather(self) -> None:
        """Update the weather display."""
        # Fetch new data
        self.weather_data = self.fetch_weather_data()
        
        if self.weather_data:
            # Top section
            art = self.get_weather_art(self.weather_data['condition'])
            greeting = self.get_greeting()
            condition = self.weather_data['condition']
            temp = f"{self.weather_data['temp']}°C"
            wind = f"Wind: {self.weather_data['wind_speed']} km/h {self.weather_data['wind_dir']}"
            humidity = f"Humidity: {self.weather_data['humidity']}%"
            
            # Bottom section - hourly forecast
            hourly = self.format_hourly_forecast(self.weather_data.get('hourly', []))
            
            # Update the widgets
            try:
                self.query_one("#weather-art").update(art)
                self.query_one("#weather-greeting").update(greeting)
                self.query_one("#weather-condition").update(condition)
                self.query_one("#weather-temp").update(temp)
                self.query_one("#weather-wind").update(wind)
                self.query_one("#weather-humidity").update(humidity)
                self.query_one("#weather-hourly").update(hourly)
            except Exception:
                pass
        else:
            # Show error message
            try:
                self.query_one("#weather-art").update(
                    "\n".join(self.WEATHER_ART['default'])
                )
                self.query_one("#weather-greeting").update("Weather Unavailable")
                self.query_one("#weather-condition").update("Unable to fetch data")
                self.query_one("#weather-temp").update("--°C")
                self.query_one("#weather-wind").update("Wind: -- km/h")
                self.query_one("#weather-humidity").update("Humidity: --%")
                self.query_one("#weather-hourly").update("Check your connection")
            except Exception:
                pass

    def on_panel_focus(self) -> None:
        """Handle when panel gains focus - force update."""
        # Only update if more than 5 minutes have passed
        now = datetime.now()
        if self.last_update is None or (now - self.last_update).seconds > 300:
            self.update_weather()
            self.last_update = now