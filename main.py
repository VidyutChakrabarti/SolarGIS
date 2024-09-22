import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import ee 
from geopy.geocoders import Photon 
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
from shapely.geometry import Polygon
from shapely.geometry import shape
from pyproj import Transformer
import shapely.ops as ops
from dotenv import load_dotenv
import os
from streamlit_extras.switch_page_button import switch_page
import asyncio
import aiohttp

load_dotenv()
api_key = os.getenv('SOLCAST_API_KEY')
st.set_page_config(layout="wide")

ee.Initialize(project = 'ee-chakrabartivr')


with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if 'lat' not in st.session_state:
    st.session_state.lat = 21.1537
if 'lng' not in st.session_state:
    st.session_state.lng = 79.0729 
if 'prev_rectangle_coords' not in st.session_state:
    st.session_state.prev_rectangle_coords = None
if 'total_area' not in st.session_state:
    st.session_state.total_area = 0
if 'bbox_center' not in st.session_state:
    st.session_state.bbox_center = None
if 'response_radiation' not in st.session_state:
    st.session_state.response_radiation = None
if 'response_pv_power' not in st.session_state:
    st.session_state.response_pv_power = None

async def fetch_data(session, url, headers):
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def main_fetch(latitude, longitude, api_key):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    url_radiation = f'https://api.solcast.com.au/world_radiation/estimated_actuals?latitude={latitude}&longitude={longitude}&hours=24'
    url_pv_power = f'https://api.solcast.com.au/world_pv_power/estimated_actuals?latitude={latitude}&longitude={longitude}&capacity=5&tilt=30&azimuth=0&hours=12'
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_data(session, url_radiation, headers),
            fetch_data(session, url_pv_power, headers)
        ]
        response_radiation, response_pv_power = await asyncio.gather(*tasks)
        
        return response_radiation, response_pv_power

buildings = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons") 
def get_rectangle_coordinates(data):
    if data and 'geometry' in data:
        coordinates = data['geometry']['coordinates'][0]
        return coordinates[:-1] 
    return []

st.sidebar.markdown('<h1 class="gradient-text">Solar Potential Prediction Estimate</h1>', unsafe_allow_html=True)

geolocator = Photon(user_agent="measurements")
with st.sidebar.form(key='my_form'):
    location_name = st.text_input("Enter a location name:")
    submit_button = st.form_submit_button(label='Search')   
if submit_button:
    try:
        loc = geolocator.geocode(location_name)
    except: 
        loc = None
        st.sidebar.write("""Geocoding API rate exceeded,
                          restrain from overusing open-source APIs. Reload and Try Again!""")
    if loc:
        st.session_state.lat = loc.latitude
        st.session_state.lng = loc.longitude
        print(f"geocoding query processed, results: {st.session_state.lat} {st.session_state.lng}.")
    else:
        st.sidebar.write("Location not found. Please try another name.")
        st.session_state.lat = 21.1537
        st.session_state.lng = 79.0729

map_location = [st.session_state.lat , st.session_state.lng] 
m = folium.Map(location=map_location, zoom_start=17, tiles=None)
google_dark_tile = folium.TileLayer(
    tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",  #1yrs = s, t, r 
    attr='Google',
    name='Google Dark',
    max_zoom=21,
    subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
)
google_dark_tile.add_to(m)
draw = Draw(
    export=False,
    draw_options={
        'rectangle': True,
        'polyline': False,
        'polygon': False,
        'circle': False,
        'marker': False,
        'circlemarker': False,
    },
    edit_options={
        'edit': True, 
        'remove': True 
    }
)
draw.add_to(m)
def add_feature_collection_to_map(m):
    buildings_image = ee.Image().paint(featureCollection=buildings, color='ffcc00', width=1)
    visualization_params = {
        'min': 0,
        'max': 1,
        'palette': ['#ffcc00']}
    map_id_dict = buildings_image.getMapId(visualization_params)
    folium.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name='Solar Potential - Building Footprints',
        overlay=True,
        control=True
    ).add_to(m)

add_feature_collection_to_map(m)


def calculate_area(buildings_in_bbox):
    areas = buildings_in_bbox.aggregate_sum('area_in_meters').getInfo()
    st.session_state.total_area = areas
    print("rooftop area", st.session_state.total_area)

def threaded_calculate_area(buildings_in_bbox):
    thread = threading.Thread(target=calculate_area, args=(buildings_in_bbox,))
    add_script_run_ctx(thread)
    thread.start()

output = st_folium(m, width='100%')
if output.get('all_drawings') and isinstance(output.get('all_drawings'), list):
    if len(output['all_drawings']) == 1:
        drawing = output['all_drawings'][0]
        if drawing['geometry']['type'] == 'Polygon':
            rectangle_coords = get_rectangle_coordinates(drawing)
            if rectangle_coords:
                st.sidebar.markdown("### Selected Coordinates:")
                sides = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]
                for side, coord in zip(sides, rectangle_coords):
                    st.sidebar.markdown(f"**{side}:** `{coord}`")
                if rectangle_coords != st.session_state.prev_rectangle_coords:
                    bbox_coords = [i for i in rectangle_coords]
                    bbox_polygon = Polygon(bbox_coords)
                    transformer = Transformer.from_crs("epsg:4326", "epsg:6933", always_xy=True)
                    transformed_polygon = ops.transform(transformer.transform, bbox_polygon)
                    area = transformed_polygon.area
                    print("geodesic area", area)
                    if(area>8000): 
                        st.sidebar.markdown("<span style='color:red'>Area constraint violated. Choose a smaller area.</span>", unsafe_allow_html=True)
                    else:
                        st.session_state.prev_rectangle_coords = rectangle_coords               
                        bounding_box = ee.Geometry.Polygon([rectangle_coords])              
                        buildings_in_bbox = buildings.filterBounds(bounding_box)
                        threaded_calculate_area(buildings_in_bbox)  
                        st.session_state.bbox_center = bbox_polygon.centroid.coords[0]
    else:
        st.sidebar.markdown("<span style='color:red'>Delete the previously selected bounding box.</span>", unsafe_allow_html=True)       
else:
    st.sidebar.write("Draw a bounding box over the area you want the solar estimation for.") 
    st.session_state.total_area = 0 
    st.session_state.bbox_center = None 

with st.sidebar.form(key='paraform', clear_on_submit=True):
    solar_panels = st.slider("Select number of solar panels installed:", 0, 50, 2)
    solar_efficiency = st.slider("Solar panel efficiency (%):", 0, 100, 1)
    module_type = st.selectbox("Module Type:", ["Monocrystalline", "Polycrystalline"])
    array_type = st.selectbox("Array Type:", ["Fixed (open rack)", "Tracking"])
    est = st.form_submit_button(label='Estimate')

    if est and st.session_state.bbox_center:
        latitude = st.session_state.bbox_center[1]
        longitude = st.session_state.bbox_center[0]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response_radiation, response_pv_power = loop.run_until_complete(main_fetch(latitude, longitude, api_key))
        
        if response_radiation and response_pv_power:
            st.session_state.response_radiation = response_radiation
            st.session_state.response_pv_power = response_pv_power
            print(response_pv_power)
            switch_page("app")
        else:
            st.error('Error fetching data from APIs')
        

    if est and st.session_state.bbox_center is None: 
        st.sidebar.error("Select a bouding box")


