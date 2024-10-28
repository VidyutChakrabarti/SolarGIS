import streamlit as st
import pydeck as pdk
import pandas as pd
import random
import numpy as np
from pvlib import location
from shapely.geometry import Polygon
from shapely.affinity import translate
import datetime
import plotly.graph_objects as go
import pytz
from pyproj import Proj, Transformer

st.set_page_config(layout="wide")
with open("finalstyle.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


if 'combined_df' not in st.session_state: 
    st.session_state.combined_df = pd.DataFrame({
        'latitudes': [
            [28.613092, 28.613215, 28.613215, 28.613092],
            [28.613292, 28.613415, 28.613415, 28.613292],
           
        ],
        'longitudes': [
            [77.210643, 77.210643, 77.210814, 77.210814],
            [77.210843, 77.210843, 77.211014, 77.211014],
            
        ],
        'estimated_height': [0, 100.12]  # Heights of structures
    })
 
combined_df = st.session_state.combined_df

if 'bbox_center' not in st.session_state:
    st.session_state.bbox_center = [77.210643,28.613215]

# Function to generate random colors for each building
def generate_color():
    return [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 200]

# Function to format the data for pydeck
def format_bbox_data(df):
    polygons = []
    for i, row in df.iterrows():
        coordinates = [[lon, lat] for lat, lon in zip(row['latitudes'], row['longitudes'])]
        coordinates.append(coordinates[0])
        polygons.append({
            'polygon': coordinates,
            'height': row['estimated_height'],
            'color': generate_color()  
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
    zoom=17,
    pitch=45,  
    bearing=0,  
)

# Add a tooltip to display building height
tooltip = {
    "html": "<b>Height:</b> {height} meters",
    "style": {"backgroundColor": "Moccasin", "color": "darkblue"},
}


st.sidebar.markdown('<h1 class="gradient-text">Partial Shading Re-estimation</h1>', unsafe_allow_html=True)
st.sidebar.button('Restart')

c1, c2= st.columns([2,1])
with c2:
    with st.form(key='redraw'):
        st.write("**Double click cells to change estiamted heights of obstacles:**") 
        st.session_state.combined_df = st.data_editor(st.session_state.combined_df)
        redraw = st.form_submit_button('Change estimated heights')
        if redraw: 
            st.rerun()

st.sidebar.text_area('AI generated Inference:', 'asijsijd', height=450)

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
current_date = datetime.date.today()
times = pd.date_range(
    start=f'{current_date} 05:00', 
    end=f'{current_date} 19:00', 
    freq='h', 
    tz=indian_timezone
)

# Get solar position data
solar_position = loc.get_solarposition(times)

from shapely.geometry import LineString

def calculate_shadow(obstacle_row, solar_zenith, solar_azimuth):
    obstacle_latitudes = list(map(float, obstacle_row['latitudes']))
    obstacle_longitudes = list(map(float, obstacle_row['longitudes']))
    
    # Convert obstacle coordinates to UTM
    obstacle_x, obstacle_y = transformer.transform(obstacle_latitudes, obstacle_longitudes)
    
    # Store shadow polygons of each side
    shadow_segments = []
    
    for i in range(len(obstacle_x)):
        # Base point and next point for each segment of the obstacle
        x1, y1 = obstacle_x[i], obstacle_y[i]
        x2, y2 = obstacle_x[(i + 1) % len(obstacle_x)], obstacle_y[(i + 1) % len(obstacle_y)]
        
        # Shadow length based on height and solar zenith angle
        shadow_length = obstacle_row['estimated_height'] / np.tan(np.radians(solar_zenith))
        
        # Shadow direction
        dx = shadow_length * np.sin(np.radians(solar_azimuth))
        dy = shadow_length * np.cos(np.radians(solar_azimuth))
        
        # Project shadow from each segment of the base
        shadow_segment = Polygon([ 
            (x1, y1), (x2, y2), 
            (x2 + dx, y2 + dy), 
            (x1 + dx, y1 + dy), 
            (x1, y1)
        ])
        shadow_segments.append(shadow_segment)
    
    # Merge segments to get the complete shadow polygon
    shadow_polygon = Polygon()
    for segment in shadow_segments:
        shadow_polygon = shadow_polygon.union(segment)
    
    return shadow_polygon


# Calculate shadow coverage percentage for each hour
shadow_coverage = []
for idx, time in enumerate(times):
    # Get solar zenith and azimuth for the current time
    solar_zenith = solar_position['apparent_zenith'].iloc[idx]
    solar_azimuth = solar_position['azimuth'].iloc[idx]
    
    if solar_zenith < 90:  # Only calculate if the sun is above the horizon
        total_shadow_area = 0
        for _, obstacle_row in obstacles.iterrows():
            # Project shadow for the obstacle
            shadow_polygon = calculate_shadow(obstacle_row, solar_zenith, solar_azimuth)
            
            # Calculate intersection with main building rooftop
            intersection_area = rooftop_polygon.intersection(shadow_polygon).area
            total_shadow_area += intersection_area
        
        # Calculate percentage coverage
        shadow_percentage = (total_shadow_area / rooftop_polygon.area) * 100
    else:
        shadow_percentage = 0  # No shadow if the sun is below the horizon
    
    shadow_coverage.append(shadow_percentage)

# Plotting the shadow coverage percentage throughout the day using Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(x=times.hour, y=shadow_coverage, mode='lines+markers', line=dict(color='teal')))
fig.update_layout(
    title="Percentage of Rooftop Shadow Coverage Throughout the Day",
    xaxis_title="Hour of the Day",
    yaxis_title="Shadow Coverage Percentage (%)",
    template="plotly_white"
)

# Display the Plotly plot in Streamlit
st.plotly_chart(fig)

with c1:
    with st.container(border=True):
        st.write("**Shadow Visualizations**")
        selected_hour = st.slider("Select hour to visualize shadows(UTC):", min_value=5, max_value=19, value=12, step=1)

def get_shadow_polygons(selected_hour):
    idx = times.hour.get_loc(selected_hour)  # Get index for the selected hour
    
    solar_zenith = solar_position['apparent_zenith'].iloc[idx]
    solar_azimuth = solar_position['azimuth'].iloc[idx]

    shadow_polygons = []

    if solar_zenith < 90:  # Only project shadows if the sun is above the horizon
        for _, obstacle_row in obstacles.iterrows():
            shadow_polygon = calculate_shadow(obstacle_row, solar_zenith, solar_azimuth)
            
            # Convert UTM shadow coordinates back to lat/lng and reverse order to [lon, lat]
            shadow_coords_utm = list(shadow_polygon.exterior.coords)
            shadow_coords_latlng = [
                transformer.transform(x, y, direction="INVERSE")[::-1] for x, y in shadow_coords_utm
            ]

            shadow_polygons.append({
                'polygon': shadow_coords_latlng,
                'color': [50, 50, 50, 150]  # Dark gray color for shadows
            })
    return shadow_polygons


# Get shadow polygons for the selected hour
shadow_data = get_shadow_polygons(selected_hour)

# Define layer for shadow polygons
shadow_layer = pdk.Layer(
    "PolygonLayer",
    shadow_data,
    get_polygon="polygon",
    get_fill_color="color",
    elevation_scale=1,
    extruded=False,
    pickable=False,
)

with c1:
    with st.container(border=True):
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/outdoors-v11",
            initial_view_state=view_state,
            layers=[layer, shadow_layer],  
        ))
