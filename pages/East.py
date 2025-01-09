import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageFile
import pandas as pd
from streamlit_extras.switch_page_button import switch_page
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import random
import time
from helperfuncs import fetch_from_session_storage, fetch_and_store_image
from streamlit_session_browser_storage import SessionStorage
browsersession = SessionStorage()

ImageFile.LOAD_TRUNCATED_IMAGES = True
st.set_page_config(layout="wide", page_title='SolarGis', page_icon = 'solargislogo.png')
from helperfuncs import alter_df

with st.empty():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 0px;
        max-width: 250px;
        }
        iframe {
        max-height: 400px;
        }
        [data-testid="column"]{
            background-color: rgba(255, 0, 149, 0.3);
            border: 2px solid rgba(255, 0, 149, 1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        [data-testid="stForm"]{
            background-color: rgba(255, 0, 149, 0.3);
            border: 2px solid rgba(255, 0, 149, 1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .main .block-container {
            padding-top: 4rem;
            padding-bottom: 0rem;
            padding-left: 2rem;
            padding-right: 1rem;
        }
        @keyframes gradient-move {
            0% { background-position: 200% 50%; }
            100% { background-position: 0% 50%; }
        }
        .gradient-text {
            background: linear-gradient(to right, #ff3300, #7bfcfe, #ff7e5f);
            background-size: 200% auto;
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradient-move 5s linear infinite;
            font-size: 25px;
            font-weight: bold;
            font-family: 'Times New Roman', Times, serif; 
        }
        .gradient-line {
            height: 10px;
            border: none;
            margin-top: 0px;
            margin-bottom: 2px;
            color: #00008B;
            background-color: #00008B;
            background-image: linear-gradient(to right, #ff3300, #7bfcfe, #ff7e5f);
            background-size: 200% auto;
            animation: gradient-move 8s linear infinite;
        }
        .stButton > button {
            width: 100%; 
            border: 2px solid rgba(255, 0, 149, 1);
        }
        @keyframes borderMove {
        0% {
            border-image: linear-gradient(0deg, #00ef9f, #5ffaff, #d20051, #8d3cff) 1;
        }

        50% {
            border-image: linear-gradient(180deg, #00ef9f, #5ffaff, #d20051, #8d3cff) 1;
        }

        100% {
            border-image: linear-gradient(360deg, #00ef9f, #5ffaff, #d20051, #8d3cff) 1;
        }
    }

    #text_area_1 {
        border: 2px solid;
        border-image-slice: 1;
        border-image: linear-gradient(90deg, #00ef9f, #5ffaff, #d20051, #8d3cff) 1;
        animation: borderMove 3s linear infinite;
    }
        </style>
        """,
        unsafe_allow_html=True
    )

placeholder = st.empty()
with placeholder:
    try:
        if 'bbox_coords' not in st.session_state: 
            fetch_from_session_storage('boxcoords', 'bbox_coords', browsersession)
            
        if 'segmented_images' not in st.session_state: 
            fetch_from_session_storage('seg', 'segmented_images', browsersession)

        if len(st.session_state.segmented_images)!=4: 
            raise ValueError("The number of segmented images is not 4.")
    except Exception as e:
        with st.spinner("An error occured... you will be re-routed. Please retry loading this page if image already segmented."):
            time.sleep(1)
        if 'rerouted' not in st.session_state: 
            st.session_state.rerouted = "East"
        switch_page('South')
        
placeholder.empty()
    
if 'bbox_center' not in st.session_state: 
    latitudes = [coord[1] for coord in st.session_state.bbox_coords]
    longitudes = [coord[0] for coord in st.session_state.bbox_coords]
    avg_lat = sum(latitudes) / len(latitudes)
    avg_lon = sum(longitudes) / len(longitudes)
    st.session_state.bbox_center = [avg_lon, avg_lat]

if 'drawing_mode' not in st.session_state:
    st.session_state.drawing_mode = "Bounding Box"
if 'annotations' not in st.session_state:
    st.session_state.annotations = []
if 'upis' not in st.session_state: 
    st.session_state.upis = ["sampleimages/1north.jpeg", "sampleimages/3west-left.jpeg", "sampleimages/5south-left.jpeg", "sampleimages/7east-left.jpeg"]
    
if 'bbox_confirmed' not in st.session_state:
    st.session_state.bbox_confirmed = False
if 'rectangle_drawn' not in st.session_state:
    st.session_state.rectangle_drawn = False
if 'line_drawn' not in st.session_state:
    st.session_state.line_drawn = False
if 'new_box' not in st.session_state: 
    st.session_state.new_box = None
if 'dt4' not in st.session_state: 
    st.session_state.dt4 = None
    
if 'east_bytes' not in st.session_state: 
    st.session_state.east_bytes = " "
if st.session_state.east_bytes == " ": 
    fetch_and_store_image(st.session_state.segmented_images[3], 'east_bytes', 'South')

def random_color():
    colors = {
        "green": "rgba(0, 128, 0, 0.3)",
        "skyblue": "rgba(135, 206, 235, 0.3)",
        "yellow": "rgba(255, 255, 0, 0.3)",
        "red": "rgba(255, 0, 0, 0.3)",
        "purple": "rgba(128, 0, 128, 0.3)"
    }
    return random.choice(list(colors.values()))

# Function to reset session state for the next round of annotation
def reset_session_state():
    st.session_state.bbox_confirmed = False
    st.session_state.rectangle_drawn = False
    st.session_state.line_drawn = False
    st.session_state.drawing_mode = "Bounding Box"

# Sidebar description
st.sidebar.markdown('<h1 class="gradient-text">Image Annotation for Height Estimation (East)</h1><hr class="gradient-line"><br>', unsafe_allow_html=True)
st.sidebar.text_area("Workflow Instructions:", """
1. Select a bounding box on the map specifying the location of the obstacle.
                     
2. Draw a rectangle on the image to represent an object for height measurement.
                     
3. Draw a reference line for height estimation. (the line drawn will be taken as a reference of how 1m looks like in the context of the object selected.)
                     
4. Repeat as needed, then press "Next Page" to move forward.
""", height=450)

c1, c2 = st.columns([1.2, 1])

with c2:
    st.write("**Step 1: Select Bounding Box on Map**")
    m = folium.Map(location=[st.session_state.bbox_center[1], st.session_state.bbox_center[0]], zoom_start=18, tiles=None)
    folium.TileLayer(tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr='Google', name='Google Dark', max_zoom=21, subdomains=['mt0', 'mt1', 'mt2', 'mt3']).add_to(m)
    draw = Draw(draw_options={"rectangle": True, "polygon": False, "circle": False, "marker": False, "polyline": False, 'circlemarker': False}, edit_options={"edit": True})
    draw.add_to(m)
    folium.Polygon(locations=[(coord[1], coord[0]) for coord in st.session_state.bbox_coords], color="blue", fill=True, fill_opacity=0.2).add_to(m)
    output = st_folium(m, width=530, height=400)
    if st.button("Confirm Bounding Box", key="confirm_bbox"):
        st.session_state.bbox_confirmed = True
        st.session_state.new_box = output["all_drawings"][-1]["geometry"]["coordinates"]
        st.session_state.drawing_mode = "Rectangle"

with c1:
    try: 
        image = Image.open(st.session_state.east_bytes)

    except Exception as e: 
        st.session_state.east_byte = " "
        st.rerun()

    canvas_result = st_canvas(
        fill_color=random_color(),
        stroke_width=2,
        stroke_color="#000",
        background_image=image,
        update_streamlit=True,
        drawing_mode="rect" if st.session_state.drawing_mode == "Rectangle" else "line",
        width=575,
        key="canvas",
    )

    # Rectangle submission
    if st.button("Select Object", key="submit_rect", disabled=(not st.session_state.bbox_confirmed or st.session_state.drawing_mode != "Rectangle"),use_container_width=True, help='Confirm bounding box first.'):
        if canvas_result.json_data:
            rect_df = pd.json_normalize(canvas_result.json_data["objects"])
            st.session_state.annotations.append({"bbox_coords": st.session_state.new_box, "rect_height": rect_df['height'].iloc[-1]})
            st.session_state.rectangle_drawn = True
            st.session_state.drawing_mode = "Line"  # Shift to line drawing
            st.rerun()

    # Line submission
    if st.button("Submit reference Line", key="submit_line", disabled=(not st.session_state.rectangle_drawn or st.session_state.drawing_mode != "Line"), use_container_width=True, help='Confirm object first.'):
        if canvas_result.json_data:
            line_df = pd.json_normalize(canvas_result.json_data["objects"])
            st.session_state.annotations[-1]["line_height"] = line_df['height'].iloc[-1]       
            st.session_state.line_drawn = True
            reset_session_state() 
            st.rerun() 


with st.form(key='df'): 
    st.write("**Collected Annotations:**")
    expand = st.expander("Note on zero obstacles to be selected.") 
    expand.write("▶ If certain images do not have any obstacles to be selected, draw a box far away from the setup site and radomly select rectangles and line such that their estimated heights would not cast any shadows that could interfere with the setup site.")
    expand.write("▶ This step has been incorporated to ensure type safety.")
    if st.session_state.annotations:
        st.dataframe(pd.DataFrame(st.session_state.annotations))

    all_annotations_complete = all(
        "bbox_coords" in ann and "line_height" in ann and "rect_height" in ann
        for ann in st.session_state.annotations
    )

    next_page = st.form_submit_button('Next Page', disabled=((not all_annotations_complete) or len(st.session_state.annotations)==0), use_container_width=True, help = "Select atleast one obstacle. If you have drawn a rectangle you must complete the row with a line.")

    if next_page:
        st.session_state.annotations = pd.DataFrame(st.session_state.annotations)
        st.session_state.dt4 = alter_df(st.session_state.annotations)
        inter_dt4 = st.session_state.dt4.to_dict(orient='records')
        browsersession.setItem("dt4",inter_dt4, key="save_dt4")
        time.sleep(1)
        
        st.session_state.new_box = None
        st.session_state.annotations = []
        reset_session_state()
        st.session_state.east_byte = " "
        switch_page('estimate')
