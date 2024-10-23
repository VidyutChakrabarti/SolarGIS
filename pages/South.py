import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageFile
import pandas as pd
from streamlit_extras.switch_page_button import switch_page
ImageFile.LOAD_TRUNCATED_IMAGES = True
st.set_page_config(layout='wide')
import random
from helperfuncs import alter_df

def random_color():
    colors = {
        "green": "rgba(0, 128, 0, 0.3)",
        "skyblue": "rgba(135, 206, 235, 0.3)",
        "yellow": "rgba(255, 255, 0, 0.3)",
        "red": "rgba(255, 0, 0, 0.3)",
        "purple": "rgba(128, 0, 128, 0.3)"
    }
    return random.choice(list(colors.values()))


st.sidebar.markdown('<h1 style="font-size: 1.5rem; margin-bottom: 0px;" class="gradient-text">Image Annotation for Height Estimation (West)</h1><hr class="gradient-line"><br>', unsafe_allow_html=True)
DRAWING_MODE_RECTANGLE = "Draw Rectangles"
DRAWING_MODE_LINE = "Draw Lines"
st.sidebar.text_area("Manual Segmentation Steps:", """
- Select bounding boxes for all the objects that need to be considered for height estimation.\n
- In the next step draw line within the boudning boxes of the objects selected giving a reference of 1m by object's scale.\n                    
- The order of drawing the lines must be same as the bounding box selection for us to estimate height of objects properly.                   
""", height=500)
# State to track which mode the user is in
if "drawing_mode" not in st.session_state:
    st.session_state.drawing_mode = DRAWING_MODE_RECTANGLE
if 'dt3' not in st.session_state: 
    st.session_state.dt3 = None
if 'upis' not in st.session_state: 
    st.session_state.upis = ["sampleimages/1north.jpeg", "sampleimages/3west-left.jpeg", "sampleimages/5south-left.jpeg", "sampleimages/7east-left.jpeg"]

if len(st.session_state.upis)!=0:
    image = Image.open(st.session_state.upis[2])
    # Mode selector and submission button
    if st.session_state.drawing_mode == DRAWING_MODE_RECTANGLE:
        submit_rectangles = st.button("Submit Frames")
    else:
        submit_lines = st.button("Submit Reference lines")

    # Create a drawable canvas based on the mode
    drawing_mode = "rect" if st.session_state.drawing_mode == DRAWING_MODE_RECTANGLE else "line"
    c1, c2 = st.columns([3,1])
    with c1: 
        canvas_result = st_canvas(
            fill_color=random_color(),  # Fill color with some transparency
            stroke_width=2,
            stroke_color="#000",
            background_image=image,
            update_streamlit=True,
            drawing_mode=drawing_mode,
            key="canvas",
        )

        # Handle rectangle mode: Display the coordinates of the drawn boxes
        if st.session_state.drawing_mode == DRAWING_MODE_RECTANGLE:
            if canvas_result.json_data is not None:
                objects = pd.json_normalize(canvas_result.json_data["objects"]) # need to convert obj to str because PyArrow
                for col in objects.select_dtypes(include=['object']).columns:
                    objects[col] = objects[col].astype("str")
                st.dataframe(objects)
            
            # Switch to line drawing mode after submitting rectangles
            if submit_rectangles:
                st.session_state.drawing_mode = DRAWING_MODE_LINE
                st.rerun()

        # Handle line mode: Display the start and end coordinates of the drawn lines
        elif st.session_state.drawing_mode == DRAWING_MODE_LINE:
            if canvas_result.json_data is not None:
                objects = pd.json_normalize(canvas_result.json_data["objects"]) # need to convert obj to str because PyArrow
                for col in objects.select_dtypes(include=['object']).columns:
                    objects[col] = objects[col].astype("str")
                st.dataframe(objects)

            # Reset the application after submitting lines
            if submit_lines:
                objects = pd.DataFrame(objects)
                columns_to_keep = ['type', 'width', 'height']  # Add the 8th column if needed
                objects = objects[columns_to_keep]
                st.session_state.drawing_mode = DRAWING_MODE_RECTANGLE
                st.session_state.dt3 = objects
                try: 
                    st.session_state.dt3 = alter_df(st.session_state.dt3)
                    st.session_state.drawing_mode = DRAWING_MODE_RECTANGLE
                    switch_page('East')
                except ValueError as error:  
                    st.error(f"Error: {str(error)}. Please ensure equal numbers of 'rect' and 'line' entries.") 
                    st.session_state.drawing_mode = DRAWING_MODE_RECTANGLE   
                
    
    with c2: 
        if st.session_state.drawing_mode == DRAWING_MODE_RECTANGLE:
            st.write("**Steps 1: Bounding Box selection**")
            st.write(" - **Select Bounding Box**: Click and drag on the canvas to draw a bounding box around the objects whose shadow needs to be considered. Ensure that the box closely aligns with the object's edges.")
            st.write("- **Undo Feature**: If you make a mistake, click the 'Undo' button to remove the last drawn bounding box.")            
            st.write("- **Order Tracking**: Bounding boxes are numbered based on the order they were drawn, so remember the order the boxes were drawn, for the next step. You can also refer the dataframe for this purpose.")
        else:
            st.write("**Steps 2: Reference Line selection**")
            st.write(" - **Draw Reference Lines**: Click and drag within the bounding box to draw a line which could approximately denote 1m in the scale of the object.")
            st.write("- **Undo Feature**: If you make a mistake, click the 'Undo' button to remove the last drawn bounding box.")            
            st.write("- **Order Tracking**: The refernce lines for each object must be drawn in the same order as the bounding boxes.")

                

st.markdown(
    """
    <style>
    [data-testid="column"]{
        background-color: rgba(0, 255, 110, 0.3);
        border: 2px solid rgba(0, 255, 110, 1);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main .block-container {
    padding-top: 5rem;
    padding-bottom: 0rem;
    padding-left: 2rem;
    padding-right: 1rem;
}
@keyframes gradient-move {
    0% {
        background-position: 200% 50%;
    }

    100% {
        background-position: 0% 50%;
    }
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
.stButton > button{
width: 74%; 
border: 2px solid rgba(0, 255, 110, 1);
</style>
    """,
    unsafe_allow_html=True
)
