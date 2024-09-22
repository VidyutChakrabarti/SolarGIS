import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import datetime
import plotly.express as px
import pandas as pd
import folium
from streamlit_folium import st_folium
import langchain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
from gradio_client import Client, handle_file

load_dotenv()
gemapi_key = os.getenv('GEMINI_API_KEY')

st.set_page_config(layout="wide")
if 'bbox_center' not in st.session_state: 
    st.session_state.bbox_center = [79.0729, 21.1537]
if 'response_radiation' not in st.session_state: 
    st.warning("Your bounding box has changed. Kindly reselect.")
    st.session_state.response_radiation = {'estimated_actuals':
            [{'ghi': 55, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T20:00:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T19:30:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T19:00:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 18, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T18:30:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T18:00:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T17:30:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 30, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T17:00:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 5, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T16:30:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 4, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 94, 'period_end': '2024-09-09T16:00:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 15, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T15:30:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 96, 'period_end': '2024-09-09T15:00:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 0, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 96, 'period_end': '2024-09-09T14:30:00.0000000Z', 'period': 'PT30M'},
            {'ghi': 16, 'ebh': 0, 'dni': 0, 'dhi': 0, 'cloud_opacity': 95, 'period_end': '2024-09-09T14:00:00.0000000Z', 'period': 'PT30M'}]}
if 'response_pv_power' not in st.session_state:
    st.session_state.response_pv_power = {'estimated_actuals': 
                    [{'pv_estimate': 1.686, 'period_end': '2024-09-16T09:00:00.0000000Z', 'period': 'PT30M'},
                    {'pv_estimate': 2.117, 'period_end': '2024-09-16T08:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 2.394, 'period_end': '2024-09-16T08:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 2.489, 'period_end': '2024-09-16T07:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 2.563, 'period_end': '2024-09-16T07:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 2.558, 'period_end': '2024-09-16T06:30:00.0000000Z', 'period': 'PT30M'},
                    {'pv_estimate': 2.51, 'period_end': '2024-09-16T06:00:00.0000000Z', 'period': 'PT30M'},
                    {'pv_estimate': 2.402, 'period_end': '2024-09-16T05:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 2.287, 'period_end': '2024-09-16T05:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 2.11, 'period_end': '2024-09-16T04:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 1.888, 'period_end': '2024-09-16T04:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 1.607, 'period_end': '2024-09-16T03:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 1.182, 'period_end': '2024-09-16T03:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 0.849, 'period_end': '2024-09-16T02:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 0.537, 'period_end': '2024-09-16T02:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 0.196, 'period_end': '2024-09-16T01:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 0.006, 'period_end': '2024-09-16T01:00:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 0, 'period_end': '2024-09-16T00:30:00.0000000Z', 'period': 'PT30M'}, 
                    {'pv_estimate': 0, 'period_end': '2024-09-16T00:00:00.0000000Z', 'period': 'PT30M'}]} 

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0, 
    api_key=gemapi_key)

system_prompt = """
You are an expert in renewable energy which gives to the point brief answers. Given the following PV power estimates in KW recorded after every 30 minutes, describe in brief how many appliances can be run from the power estimates.(no need to be precise, give a general list of appliances in brief.). Your responses must not exceed 100 words.
"""    
prompt_template = PromptTemplate(
    input_variables=["pv_data"],
    template=system_prompt + "\n\n{pv_data}"
)

with open("style2.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

left_col,right_col = st.columns([1.3, 2])

def infer(pv_data):
    res = llm.invoke(prompt_template.format(pv_data=pv_data))
    st.sidebar.text_area('AI generated Inference:',res.content, height=400)

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
        data = st.session_state.response_pv_power['estimated_actuals']
        times = [datetime.strptime(entry["period_end"], "%Y-%m-%dT%H:%M:%S.%f0Z").strftime('%H:%M') for entry in data]
        pv_estimates = [entry["pv_estimate"] for entry in data]
        
        df = pd.DataFrame({'Time': times, 'PV Estimate': pv_estimates})
        df = df.sort_values('Time')
        
        fig = px.line(df, x='Time', y='PV Estimate', title='Estimated PV Power Output',
                    labels={'Time': 'Time (hours)', 'PV Estimate': 'PV Estimate (kW)'},
                    color_discrete_sequence=px.colors.sequential.Blues,
                    markers=True)
        
        fig.update_layout(
            yaxis=dict(range=[0, max(pv_estimates) + 1]),
            xaxis=dict(tickmode='linear', tick0=0, dtick=1),
            template='plotly_white',
        )
        st.plotly_chart(fig)
        
        pv_data = df.to_json(orient='records')
        # Re-estimated calculations after image segmentation display
        st.markdown('<div class="container">Re-estimated Calculation After Image Segmentation Display</div>', unsafe_allow_html=True)
        st.write("Placeholder for re-estimated calculations")
        st.image('placeholder.png')
        st.form_submit_button("re-calculate")
        infer(pv_data)

with right_col:
    with st.form(key="graph"):
        st.markdown('<div class="container">Graph Display</div>', unsafe_allow_html=True)
        data = st.session_state.response_radiation['estimated_actuals']
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
        c1,c2 = st.columns([4,1])
        with c1:
            st.slider("Time range:", 1, 24, 24)
        with c2:
            st.markdown(" ")
            st.markdown(" ")
            st.form_submit_button("Redraw",use_container_width=True)

    with st.form(key="image"):
        st.markdown('<div class="controls-container">SEGMENTATION CONTROLS</div>', unsafe_allow_html=True)

        uploaded_image = st.file_uploader("Upload an image for segmentation", type=["jpg", "png", "jpeg"])

        if uploaded_image:
            save_dir = "uploaded_images"
            os.makedirs(save_dir, exist_ok=True)
            
            file_path = os.path.join(save_dir, uploaded_image.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_image.read())
            with st.spinner("Your image is being segmented..."):
                client = Client("https://evitsam.hanlab.ai/")
                result = client.predict(
                    param_0=handle_file(file_path),
                    param_2=64,
                    param_3=0.8,
                    param_4=0.85,
                    param_5=0.7,
                    api_name="/lambda_3"
                )
                st.image(result, caption="Segmented Image", use_column_width=True)
            os.remove(file_path)    

        c1,c2,c3,c4 = st.columns([2,1.8,0.1,1])
        with c1:
            st.slider("Adjust height:", 0, 100, 50)
        with c2: 
            st.selectbox("Type of image:", ['LiDar(Iphone)', 'Stereo'])
        with c4:
            st.markdown(" ")
            st.markdown(" ")
            st.form_submit_button("submit",use_container_width=True)
