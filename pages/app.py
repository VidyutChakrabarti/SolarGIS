import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import datetime
import plotly.express as px
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
#st.session_state.bbox_center = [79.0729,21.1537]
with open("style2.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

left_col, spacer, right_col = st.columns([1.2, 0.1, 2])

go_back = st.sidebar.button("Re-select Bounding box", use_container_width=True)

if go_back: 
    switch_page('main')

st.sidebar.write("Your selected bounding box:")
m = folium.Map(location=[st.session_state.bbox_center[1], st.session_state.bbox_center[0]], zoom_start=14)

folium.Marker([st.session_state.bbox_center[1], st.session_state.bbox_center[0]], popup="Location").add_to(m)

with st.sidebar:
    st_folium(m, width=300, height=200)

with left_col:
    with st.form(key="calc"):
        st.markdown('<div class="container">Initial Calculations Display</div>', unsafe_allow_html=True)
        st.write("Placeholder for initial calculations")

        # Re-estimated calculations after image segmentation display
        st.markdown('<div class="container">Re-estimated Calculation After Image Segmentation Display</div>', unsafe_allow_html=True)
        st.write("Placeholder for re-estimated calculations")
        st.form_submit_button("re-calculate")

    with st.form(key="image"):
        st.markdown('<div class="controls-container">IMAGE CONTROLS</div>', unsafe_allow_html=True)

        uploaded_image = st.file_uploader("Upload an image for segmentation", type=["jpg", "png", "jpeg"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)

        st.slider("Adjust height:", 0, 100, 50)
        st.form_submit_button("submit")

with right_col:
    with st.form(key="graph"):
        st.markdown('<div class="container">Graph Display</div>', unsafe_allow_html=True)
        data = st.session_state.response['estimated_actuals']
        # data =[ 
        #     {'ghi': 55, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T20:00:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T19:30:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T19:00:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 18, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T18:30:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T18:00:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T17:30:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 30, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T17:00:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 5, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T16:30:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 4, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T16:00:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 15, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T15:30:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 96, 'period_end': '2024-09-09T15:00:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 96, 'period_end': '2024-09-09T14:30:00.0000000Z', 'period': 'PT30M'},
        #     {'ghi': 16, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T14:00:00.0000000Z', 'period': 'PT30M'}
        # ]
        times = [datetime.strptime(entry["period_end"], "%Y-%m-%dT%H:%M:%S.%f0Z").strftime('%H:%M') for entry in data]
        ghi_values = [entry["ghi"] for entry in data]
        df = pd.DataFrame({'Time': times, 'GHI': ghi_values})
        df = df.sort_values('Time')
        fig = px.line(df, x='Time', y='GHI', title='Horizaontal Solar Irradiance',
                    labels={'Time': 'Time (hours)', 'GHI': 'GHI'},
                    color_discrete_sequence=px.colors.sequential.Reds,
                    markers=True)
        fig.update_layout(
            yaxis=dict(range=[0, max(ghi_values) + 10]),
            xaxis=dict(tickmode='linear', tick0=0, dtick=1),
            template='plotly_white',
        )
        st.plotly_chart(fig)
        st.form_submit_button("Redraw")
