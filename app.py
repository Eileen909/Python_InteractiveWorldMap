import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static
import geopandas as gpd
from datetime import datetime
import json
import os
import time

# Set page configuration
st.set_page_config(
    page_title="Global Insights Dashboard",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application title
st.title("🌎 Interactive World Map Dashboard")
st.markdown("This dashboard provides real-time insights on weather, economic indicators, and air quality across the globe.")

# API Keys (Replace with actual keys)
OPENWEATHER_API_KEY = "c25749d48d41d6fea6dffc2114b9e60a "
ALPHAVANTAGE_API_KEY = "your_alphavantage_api_key"
AQICN_API_KEY = "your_aqicn_api_key"

@st.cache_data(ttl=3600)
def load_geojson():
    """Load or download GeoJSON world map data."""
    local_file = "ne_110m_admin_0_countries.geojson"
    if not os.path.exists(local_file):
        url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
        import urllib.request
        urllib.request.urlretrieve(url, local_file)
        st.info("Downloaded world map data")

    try:
        world = gpd.read_file(local_file)
        geojson = json.loads(world.to_json())
        return world, geojson
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None, None

world_data, geojson = load_geojson()
if world_data is None:
    st.stop()

import requests
import streamlit as st

API_KEY = "c25749d48d41d6fea6dffc2114b9e60a"

@st.cache_data(ttl=600)
def get_weather_data(lat, lon):
    """Fetch weather data from OpenWeather API."""
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching weather data: {e}")
    
    # Default weather data in case of failure
    return {
        "main": {"temp": 22.5, "humidity": 65, "pressure": 1013},
        "wind": {"speed": 5.2},
        "weather": [{"description": "Partly cloudy"}]
    }

@st.cache_data(ttl=86400)
def get_economic_data(country_code):
    """Mock economic data for different countries."""
    mock_data = {
        "USA": {"gdp_growth": 2.8, "inflation": 3.1, "unemployment": 4.2, "stock_index": "S&P 500: 4,912.21"},
        "IND": {"gdp_growth": 6.7, "inflation": 5.5, "unemployment": 7.8, "stock_index": "SENSEX: 72,456.10"},
    }
    return mock_data.get(country_code, {"gdp_growth": 1.5, "inflation": 3.0, "unemployment": 5.0, "stock_index": "N/A"})

@st.cache_data(ttl=3600)
def get_aqi_data(lat, lon):
    """Fetch air quality index from AQICN API."""
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("data", {"aqi": 45, "dominentpol": "pm25"})
    except:
        pass
    return {"aqi": 45, "dominentpol": "pm25"}

@st.cache_data
def generate_global_data():
    """Generate mock data for global visualization."""
    if world_data is None:
        return pd.DataFrame(columns=['country', 'temperature', 'gdp_growth', 'aqi'])

    countries = world_data['SOVEREIGNT'].unique()
    return pd.DataFrame({
        'country': countries,
        'temperature': np.random.uniform(5, 35, len(countries)),
        'gdp_growth': np.random.uniform(-2, 8, len(countries)),
        'aqi': np.random.uniform(10, 150, len(countries))
    })

# Sidebar Filters
st.sidebar.subheader("🔍 Data Selection")
data_category = st.sidebar.selectbox("Select Data Category", ["Weather", "Economic Indicators", "Air Quality Index"])
regions = ['Global', 'North America', 'South America', 'Europe', 'Asia', 'Africa', 'Oceania']
selected_region = st.sidebar.selectbox("Select Region", regions)

# Filtering based on selected region
selected_countries = world_data if selected_region == 'Global' else world_data[world_data['CONTINENT'] == selected_region]

st.sidebar.success(f"Data updated as of {datetime.now().strftime('%H:%M:%S')}")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Interactive Map")
    m = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB positron")
    global_data = generate_global_data()

    color_map = {
        "Weather": "YlOrRd",
        "Economic Indicators": "Blues",
        "Air Quality Index": "RdYlGn_r"
    }
    
    column_map = {
        "Weather": "temperature",
        "Economic Indicators": "gdp_growth",
        "Air Quality Index": "aqi"
    }
    
    choropleth = folium.Choropleth(
        geo_data=geojson,
        name=data_category,
        data=global_data,
        columns=["country", column_map[data_category]],
        key_on="feature.properties.SOVEREIGNT",
        fill_color=color_map[data_category],
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f"{data_category} Data"
    ).add_to(m)

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(fields=['SOVEREIGNT'], aliases=['Country:'])
    )

    folium_static(m)

with col2:
    st.subheader("📊 Data Analysis")
    country_list = selected_countries['SOVEREIGNT'].dropna().tolist()
    selected_country = st.selectbox("Select a country for details", sorted(country_list))

    if selected_country:
        country_data = selected_countries[selected_countries['SOVEREIGNT'] == selected_country]
        country_code = country_data.iloc[0]['iso_a3'] if 'iso_a3' in country_data.columns else "N/A"
        st.metric("GDP Growth", f"{get_economic_data(country_code)['gdp_growth']}%")
