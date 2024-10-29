import streamlit as st
import pydeck as pdk
import pandas as pd
import random
from datetime import datetime, timedelta
import numpy as np
from pvlib import location
from shapely.geometry import Polygon
import plotly.graph_objects as go
import pytz
from pyproj import Proj, Transformer
from streamlit_extras.switch_page_button import switch_page
import asyncio
from helperfuncs import main_fetch
from data import *
import plotly.express as px
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os

load_dotenv()
api_key = os.getenv('SOLCAST_API_KEY')
gemapi_key = os.getenv('GEMINI_API_KEY')
st.set_page_config(layout="wide")
with open("finalstyle.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

youtube_code = '''
<div style="width:100%; height:auto; max-width:560px; overflow:hidden;">
  <iframe id="ytplayer" 
          src="https://www.youtube.com/embed/NLO9w963Aj0?autoplay=1&mute=1&loop=1&playlist=NLO9w963Aj0" 
          frameborder="0" 
          allow="autoplay; encrypted-media" 
          allowfullscreen
          style="width:100%; height:300px;">
  </iframe>
</div>
'''
if 'infer' not in st.session_state:
    st.session_state.infer = True
if 'res' not in st.session_state: 
    st.session_state.res = None

if 'combined_df' not in st.session_state:
    st.session_state.combined_df = pd.DataFrame({
        'latitudes': [
            [28.613092, 28.613215, 28.613215, 28.613092],  
            [28.613092, 28.613215, 28.613215, 28.613092],   
            [28.613292, 28.613415, 28.613415, 28.613292],   
            [28.613192, 28.613315, 28.613315, 28.613192],   
            [28.612992, 28.613115, 28.613115, 28.612992],   
        ],
        'longitudes': [
            [77.210643, 77.210643, 77.210814, 77.210814],   
            [77.210843, 77.210843, 77.211014, 77.211014],   
            [77.210743, 77.210743, 77.210914, 77.210914],   
            [77.210843, 77.210843, 77.211014, 77.211014],   
            [77.210543, 77.210543, 77.210714, 77.210714],   
        ],
        'estimated_height': [0, 10.2, 9.8, 8.5, 24.5]  # Heights of structures
    })
if 'response_radiation' not in st.session_state:
    st.session_state.response_radiation = radiance_data
if 'response_pv_power' not in st.session_state:
    st.session_state.response_pv_power = pv_data

combined_df = st.session_state.combined_df

if 'bbox_center' not in st.session_state:
    st.session_state.bbox_center = [77.210643,28.613215]

# Function to generate random colors for each building
def generate_color():
    return [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 200]

def format_bbox_data(df):
    polygons = []
    for i, row in df.iterrows():
        coordinates = [[lon, lat] for lat, lon in zip(row['latitudes'], row['longitudes'])]
        coordinates.append(coordinates[0])  # Closing the loop for the polygon
        building_type = "Main Building" if i == 0 else f"Obstacle {i}"
        polygons.append({
            'polygon': coordinates,
            'height': row['estimated_height'],
            'color': generate_color(),
            'type': building_type
        })
    return polygons

# Preparing the data for PyDeck
bbox_data = format_bbox_data(combined_df)

# Defining the layer for bounding boxes (PolygonLayer)
layer = pdk.Layer(
    "PolygonLayer",
    bbox_data,
    get_polygon="polygon",
    get_fill_color="color",  # Assigning different colors to each building
    get_elevation="height",
    elevation_scale=1,
    extruded=True,  # Make it 3D
    wireframe=True,
    pickable=True,
)

# Set the view to initial location and zoom level, with fixed pitch and bearing
view_state = pdk.ViewState(
    latitude=st.session_state.bbox_center[1],  
    longitude=st.session_state.bbox_center[0],  
    zoom=18,
    pitch=45,  
    bearing=290,  
)

tooltip = {
    "html": "<b>Building Type:</b> {type}<br><b>Reference height:</b> {height} meters",
    "style": {"backgroundColor": "Moccasin", "color": "darkblue"},
}


st.sidebar.markdown('<h1>Partial Shading Re-estimation</h1>', unsafe_allow_html=True)
restart = st.sidebar.button('Restart')
if restart: 
    switch_page('main')

c1, c2= st.columns([0.9,1])
with c1:
    with st.form(key='redraw'):
        st.write("**Double click cells to change estiamted heights of obstacles:**") 
        st.session_state.combined_df = st.data_editor(st.session_state.combined_df)
        redraw = st.form_submit_button('Change estimated heights')
        if redraw:
            st.session_state.infer = True 
            st.rerun()
    st.write(youtube_code, unsafe_allow_html=True)

# Function to determine UTM zone based on longitude
def get_utm_zone(longitude):
    # Calculate UTM zone number based on longitude
    zone_number = int((longitude + 180) / 6) + 1
    return zone_number

# Load DataFrame from session state
df = st.session_state.combined_df

# Extract main building and obstacles data
main_building = df.iloc[0]
obstacles = df.iloc[1:]

# Parse main building latitudes and longitudes
main_latitudes = list(map(float, main_building['latitudes']))
main_longitudes = list(map(float, main_building['longitudes']))
main_height = main_building['estimated_height']

# Average longitude to determine the UTM zone for the main building
average_longitude = np.mean(main_longitudes)
utm_zone = get_utm_zone(average_longitude)
proj_utm = Proj(proj="utm", zone=utm_zone, datum="WGS84", hemisphere="north")
proj_wgs84 = Proj("epsg:4326")

# Set up Transformer for coordinate conversion
transformer = Transformer.from_proj(proj_wgs84, proj_utm)

# Convert lat/lon to the dynamically determined UTM projection
main_x, main_y = transformer.transform(main_latitudes, main_longitudes)
rooftop_polygon = Polygon(zip(main_x, main_y))

# Set up location and times for sun position calculation with IST timezone
indian_timezone = pytz.timezone("Asia/Kolkata")
loc = location.Location(latitude=np.mean(main_latitudes), longitude=average_longitude)
current_date = datetime.today().date()
times = pd.date_range(
    start=f'{current_date} 05:00', 
    end=f'{current_date} 19:00', 
    freq='30min', 
    tz=indian_timezone
)

# Get solar position data
solar_position = loc.get_solarposition(times)

def calculate_shadow(obstacle_row, solar_zenith, solar_azimuth):
    obstacle_latitudes = list(map(float, obstacle_row['latitudes']))
    obstacle_longitudes = list(map(float, obstacle_row['longitudes']))
    obstacle_x, obstacle_y = transformer.transform(obstacle_latitudes, obstacle_longitudes)
    shadow_segments = []
    
    for i in range(len(obstacle_x)):
        x1, y1 = obstacle_x[i], obstacle_y[i]
        x2, y2 = obstacle_x[(i + 1) % len(obstacle_x)], obstacle_y[(i + 1) % len(obstacle_y)]
        shadow_length = obstacle_row['estimated_height'] / np.tan(np.radians(solar_zenith))
        dx = shadow_length * np.sin(np.radians(solar_azimuth))
        dy = shadow_length * np.cos(np.radians(solar_azimuth))
        
        shadow_segment = Polygon([ 
            (x1, y1), (x2, y2), 
            (x2 + dx, y2 + dy), 
            (x1 + dx, y1 + dy), 
            (x1, y1)
        ])
        shadow_segments.append(shadow_segment)
    
    shadow_polygon = Polygon()
    for segment in shadow_segments:
        shadow_polygon = shadow_polygon.union(segment)
    
    return shadow_polygon


shadow_coverage = []
for idx, time in enumerate(times):
    # Get solar zenith and azimuth for the current time
    solar_zenith = solar_position['apparent_zenith'].iloc[idx]
    solar_azimuth = solar_position['azimuth'].iloc[idx]
    
    if solar_zenith < 90:  
        total_shadow_area = 0
        for _, obstacle_row in obstacles.iterrows():
            shadow_polygon = calculate_shadow(obstacle_row, solar_zenith, solar_azimuth)
            
            intersection_area = rooftop_polygon.intersection(shadow_polygon).area
            total_shadow_area += intersection_area
    
        shadow_percentage = (total_shadow_area / rooftop_polygon.area) * 100
    else:
        shadow_percentage = 0  
    
    shadow_coverage.append(shadow_percentage)

with c2:
    selected_hour = st.slider(
    "**Select time to visualize shadows (UTC):**",
    min_value=5.0,
    max_value=19.0,
    value=12.0,
    step=0.5,
    format="%.1f"
)    

def get_shadow_polygons(selected_hour):
    idx = int((selected_hour - 5) * 2) 
    solar_zenith = solar_position['apparent_zenith'].iloc[idx]
    solar_azimuth = solar_position['azimuth'].iloc[idx]

    shadow_polygons = []

    if solar_zenith < 90:
        for _, obstacle_row in obstacles.iterrows():
            shadow_polygon = calculate_shadow(obstacle_row, solar_zenith, solar_azimuth)
            shadow_coords_utm = list(shadow_polygon.exterior.coords)
            shadow_coords_latlng = [
                transformer.transform(x, y, direction="INVERSE")[::-1] for x, y in shadow_coords_utm
            ]

            shadow_polygons.append({
                'polygon': shadow_coords_latlng,
                'color': [50, 50, 50, 150]  
            })
    return shadow_polygons

shadow_data = get_shadow_polygons(selected_hour)

shadow_layer = pdk.Layer(
    "PolygonLayer",
    shadow_data,
    get_polygon="polygon",
    get_fill_color="color",
    elevation_scale=1,
    extruded=False,
    pickable=False,
)

with c2:
    with st.container(border=True):
        st.write("**Shadow Visualizations**")
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/outdoors-v11",
            initial_view_state=view_state,
            layers=[layer, shadow_layer],
            tooltip=tooltip  
        ))
col1, col2 = st.columns([2,1])
with col2:
    fig = go.Figure()
    shadow_times = times.strftime('%H:%M')
    shadow_df = pd.DataFrame({'Time': shadow_times, 'Shadow Coverage (%)': shadow_coverage})
    fig.add_trace(go.Scatter(x=times.strftime('%H:%M'), y=shadow_coverage, mode='lines+markers', line=dict(color='lavender')))
    fig.update_layout(
        title="Percentage of Rooftop Shadow Coverage",
        xaxis_title="Time of the Day",
        yaxis_title="Shadow Coverage Percentage (%)",
        xaxis=dict(dtick=2,tickangle=-45),
        height=350  
    )
    with st.container(border=True):
        st.plotly_chart(fig)
    st.selectbox('Type of connection between panels:', ['Series', 'Parallel'])


with col1:
    with st.form('solar'):
        data = st.session_state.response_pv_power['estimated_actuals']
        times = [(datetime.strptime(entry["period_end"], "%Y-%m-%dT%H:%M:%S.%f0Z") + timedelta(hours=5, minutes=30)).strftime('%H:%M') for entry in data]
        pv_estimates = [entry["pv_estimate"] for entry in data]
        
        df = pd.DataFrame({'Time': times, 'PV Estimate': pv_estimates})
        df = df.sort_values('Time')
        
        adjusted_df = pd.merge(df, shadow_df, on='Time', how='inner')
        
        adjusted_df['Adjusted PV Estimate'] = adjusted_df.apply(
            lambda row: max(row['PV Estimate'] * (1 - row['Shadow Coverage (%)'] / 100), 0), axis=1
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=adjusted_df['Time'], y=adjusted_df['PV Estimate'], mode='lines+markers', name='Original PV Estimate',
            line=dict(color='lightgreen'), marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=adjusted_df['Time'], y=adjusted_df['Adjusted PV Estimate'], mode='lines+markers', name='Adjusted PV Estimate',
            line=dict(color='salmon'), marker=dict(size=6)
        ))

        fig.update_layout(
            title="Estimated PV Power Output (with Partial Shading Impact)",
            xaxis_title="Time of the Day",
            yaxis_title="PV Estimate (kW)",
            xaxis=dict(dtick=2, tickangle=-45),
            yaxis=dict(range=[0, max(adjusted_df['PV Estimate']) + 1]),
            height=400
        )

        st.plotly_chart(fig)

        refetch = st.form_submit_button('Re-Fetch')
        if refetch:
            lati = st.session_state.bbox_center[1]
            longi = st.session_state.bbox_center[0]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response_radiation, response_pv_power = loop.run_until_complete(main_fetch(lati, longi, api_key))
                resp = response_pv_power['estimated_actauls']
            except Exception as e:
                st.error('Error fetching data from APIs')
                response_radiation, response_pv_power = None, None
            if response_pv_power and response_radiation:    
                st.session_state.response_radiation = response_radiation
                st.session_state.response_pv_power = response_pv_power

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0, 
    api_key=gemapi_key)

system_prompt = """
You are an expert in renewable energy which gives to the point brief answers. Given the following adjusted PV power estimates in KW recorded after every 30 minutes, describe in brief how many appliances can be run from the adjusted power estimates.(no need to be precise, give a general list of appliances in brief.). Your responses must not exceed 100 words.
"""    
prompt_template = PromptTemplate(
    input_variables=["pv_data"],
    template=system_prompt + "\n\n{pv_data}"
)

def infer(pv_data):
    if st.session_state.infer:
        st.session_state.res = llm.invoke(prompt_template.format(pv_data=pv_data))
        st.session_state.infer = False
    st.sidebar.text_area('AI generated Inference:',st.session_state.res.content, height=450)
with st.sidebar:
    with st.spinner('AI will respond shortly...'):
        infer(adjusted_df)    

    
    
            
    
        
            


