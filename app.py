import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, MiniMap
import ee 
from geopy.geocoders import Photon

st.set_page_config(layout="wide")
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

ee.Initialize(project='ee-chakrabartivr')
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
        st.write("Geocoding API rate exceeded, restrain from overusing open-source APIs. Reload and Try Again!")
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
minimap = MiniMap(toggle_display=True)
minimap.add_to(m)

def calculate_area(rectangle_coords):
    st.session_state.prev_rectangle_coords = rectangle_coords               
    bounding_box = ee.Geometry.Polygon([rectangle_coords])              
    buildings_in_bbox = buildings.filterBounds(bounding_box)
    areas = buildings_in_bbox.aggregate_array('area_in_meters').getInfo()
    for area in areas:
        st.session_state.total_area += area
    print("total area", st.session_state.total_area)
    

output = st_folium(m, width='100%', height=690)
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
                    calculate_area(rectangle_coords)  
    else:
        st.sidebar.write("Delete the previously selected bounding box.")        
else:
    st.sidebar.write("Draw a bounding box over the area you want the solar estimation for.") 
    st.session_state.total_area = 0  

with st.sidebar.form(key='paraform',clear_on_submit=True): 
    solar_panels = st.slider("Select number of solar panels installed:", 0, 50, 2)
    solar_efficiency = st.slider("Solar panel efficiency (%):", 0, 100, 1)
    sub = st.form_submit_button(label='Estimate') 



