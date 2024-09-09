import streamlit as st
from streamlit_extras.switch_page_button import switch_page

with open("style2.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

left_col, spacer, right_col = st.columns([1.2,0.1, 2])

go_back = st.sidebar.button("Re-select Bounding box", use_container_width= True)
if go_back: 
    switch_page('main')

st.sidebar.write("Your selected bounding box:")

with left_col:
        # Initial calculations display
    with st.form(key="calc"):
        st.markdown('<div class="container">Initial Calculations Display</div>', unsafe_allow_html=True)
        st.write("Placeholder for initial calculations")

            # Re-estimated calculations after image segmentation display
        st.markdown('<div class="container">Re-estimated Calculation After Image Segmentation Display</div>', unsafe_allow_html=True)
        st.write("Placeholder for re-estimated calculations")
        st.form_submit_button("re-calculate")

        # Image controls
    with st.form(key = "image"):
        st.markdown('<div class="controls-container">IMAGE CONTROLS</div>', unsafe_allow_html=True)
            
        uploaded_image = st.file_uploader("Upload an image for segmentation", type=["jpg", "png", "jpeg"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)

        st.slider("Adjust height:", 0, 100, 50)
        st.form_submit_button("submit")


with right_col:
        # Graph display
    with st.form(key = "graph"):
        st.markdown('<div class="container">Graph Display</div>', unsafe_allow_html=True)
        st.line_chart({"Solar irradiance": [0.2, 0.4, 0.6, 0.8, 1.0], "Wind speed": [0.8, 0.6, 0.4, 0.2, 0.1]})

        # Graph controls
        st.slider("Select Time Range:", 0, 24, (6, 18))
        st.form_submit_button("Update")

        