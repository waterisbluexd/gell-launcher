#!/usr/bin/env python3
"""Weather panel for Gell Launcher."""

import requests
import json
from datetime import datetime, timedelta
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

    # Cache duration: 1 hour
    CACHE_DURATION = timedelta(hours=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weather_data = None
        self.last_fetch_time = None
        self.is_fetching = False

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
                    yield Static("Loading...", id="weather-condition", classes="weather-condition")
                    yield Static("--°C", id="weather-temp", classes="weather-temp-main")
                    yield Static("Wind: -- km/h", id="weather-wind", classes="weather-info-detail")
                    yield Static("Humidity: --%", id="weather-humidity", classes="weather-info-detail")
        
        # Bottom section - hourly forecast
        yield Static("Loading forecast...", id="weather-hourly", classes="weather-hourly")

    def on_mount(self) -> None:
        """Fetch weather once on mount."""
        self.update_weather()

    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid (less than 1 hour old)."""
        if self.weather_data is None or self.last_fetch_time is None:
            return False
        
        time_since_fetch = datetime.now() - self.last_fetch_time
        return time_since_fetch < self.CACHE_DURATION

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
        """Fetch weather data using wttr.in API with location from IP address."""
        try:
            # Get location from IP address
            location_response = requests.get('https://ipinfo.io/json', timeout=3)
            location_data = location_response.json()
            city = location_data.get('city', '')

            # Use requests library with timeout
            response = requests.get(
                f'https://wttr.in/{city}?format=j1',
                timeout=3,
                headers={'User-Agent': 'curl'}
            )
            
            if response.status_code == 200:
                data = response.json()
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
                    'hourly': hourly
                }
        except requests.exceptions.RequestException:
            pass
        except Exception:
            pass
        
        return None

    def format_hourly_forecast(self, hourly_data: list) -> str:
        """Format hourly forecast data showing next 6 hours from now."""
        if not hourly_data:
            return "No forecast data available"

        now = datetime.now()
        current_hour = now.hour

        # Get next 6 time slots starting from the next 3-hour interval
        forecast_hours = []
        start_hour = ((current_hour // 3) + 1) * 3

        for i in range(6):
            target_hour = (start_hour + i * 3) % 24
            time_slot = target_hour * 100

            # Find the corresponding data
            hour_data = None
            for h in hourly_data:
                h_time = int(h.get('time', '0'))
                if h_time == time_slot:
                    hour_data = h
                    break
            
            if hour_data:
                forecast_hours.append((target_hour, hour_data))

        if not forecast_hours:
            return "No forecast data available"
        
        lines = []
        
        # Time row with corrected AM/PM formatting
        times = []
        for hour_num, _ in forecast_hours:
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
        temps = [f"{h.get('tempC', 'N/A')}°" for _, h in forecast_hours]
        lines.append("  ".join(f"{t:>5}" for t in temps))
        
        # Wind row
        winds = [f"{h.get('windspeedKmph', 'N/A')}kph" for _, h in forecast_hours]
        lines.append("  ".join(f"{w:>5}" for w in winds))
        
        # Precipitation/Humidity row
        precips = [f"{h.get('precipMM', '0')}mm" for _, h in forecast_hours]
        lines.append("  ".join(f"{p:>5}" for p in precips))
        
        return "\n".join(lines)

    def update_weather(self) -> None:
        """Update the weather display with caching."""
        # Use cache if valid
        if self.is_cache_valid():
            self._refresh_display()
            return
        
        # Prevent concurrent fetches
        if self.is_fetching:
            return
            
        self.is_fetching = True
        
        # Fetch new data
        new_data = self.fetch_weather_data()
        
        if new_data:
            self.weather_data = new_data
            self.last_fetch_time = datetime.now()
            self._refresh_display()
        else:
            # Show error message only if we have no cached data
            if not self.weather_data:
                self._show_error()
        
        self.is_fetching = False

    def _refresh_display(self):
        """Refresh display with current weather data."""
        if not self.weather_data:
            return
            
        try:
            # Top section
            art = self.get_weather_art(self.weather_data['condition'])
            greeting = self.get_greeting()
            condition = self.weather_data['condition']
            temp = f"{float(self.weather_data['temp']):.0f}°C"
            wind = f"Wind: {self.weather_data['wind_speed']} km/h {self.weather_data['wind_dir']}"
            humidity = f"Humidity: {self.weather_data['humidity']}%"
            
            # Bottom section - hourly forecast
            hourly = self.format_hourly_forecast(self.weather_data.get('hourly', []))
            
            # Update the widgets
            self.query_one("#weather-art").update(art)
            self.query_one("#weather-greeting").update(greeting)
            self.query_one("#weather-condition").update(condition)
            self.query_one("#weather-temp").update(temp)
            self.query_one("#weather-wind").update(wind)
            self.query_one("#weather-humidity").update(humidity)
            self.query_one("#weather-hourly").update(hourly)
        except (ValueError, KeyError):
            self._show_error()

    def _show_error(self):
        """Show error message when weather fetch fails."""
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
        """Handle when panel gains focus - update if cache expired."""
        if not self.is_cache_valid() and not self.is_fetching:
            # Update in background without blocking
            self.run_worker(self._background_update, exclusive=True)
        else:
            # Just refresh the display with cached data (updates greeting)
            self._refresh_display()
    
    def _background_update(self):
        """Background worker to fetch weather data."""
        self.update_weather()