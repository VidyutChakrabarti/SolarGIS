import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import datetime
import plotly.express as px
import pandas as pd
import folium
from streamlit_folium import st_folium
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
from gradio_client import Client, handle_file
from data import * 

load_dotenv()
gemapi_key = os.getenv('GEMINI_API_KEY')

st.set_page_config(layout="wide")
if 'bbox_center' not in st.session_state: 
    st.session_state.bbox_center = [79.0729, 21.1537]
if 'response_radiation' not in st.session_state: 
    st.warning("Your bounding box has changed. Kindly reselect.")
    st.session_state.response_radiation = radiance_data
if 'response_pv_power' not in st.session_state:
    st.session_state.response_pv_power = pv_data
if 'dsb2' not in st.session_state:
    st.session_state.dsb2 = True

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

left_col,right_col = st.columns([1.9,2])

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
        st.markdown('<div class="container">Initial PV Output</div>', unsafe_allow_html=True)
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
            xaxis=dict(tickmode='linear', tick0=0, dtick=2, tickangle=-45),
            template='plotly_white',
            height=360
        )
        st.plotly_chart(fig)
        pv_data = df.to_json(orient='records')
        c1,c2 = st.columns([3,1])
        with c1:
            st.slider("Time range:", 1, 24, 24)
        with c2:
            st.markdown(" ")
            st.markdown(" ")
            st.form_submit_button("Re-calculate",use_container_width=True)
        infer(pv_data)

    with st.form(key="img"):
        st.markdown('<div class="container">Image uploader</div>', unsafe_allow_html=True)
        uploaded_image = st.file_uploader("Upload an image for segmentation", type=["jpg", "png", "jpeg"]) 
        c1, c2 = st.columns([2.5,1])
        with c1:
            st.selectbox("Type of image:", ['LiDar(Iphone)', 'Stereo']) 
        with c2:
            st.markdown(" ")
            st.markdown(" ")
            submit_image = st.form_submit_button("Submit Image", use_container_width=True)

with right_col:
    with st.form(key="graph"):
        st.markdown('<div class="container">Solar Irradiance Data</div>', unsafe_allow_html=True)
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
            xaxis=dict(tickmode='linear', tick0=0, dtick=2,tickangle=-50),
            template='plotly_white',
            height=360
        )
        st.plotly_chart(fig)
        c1,c2 = st.columns([4,1])
        with c1:
            st.slider("Time range:", 1, 24, 24)
        with c2:
            st.markdown(" ")
            st.markdown(" ")
            st.form_submit_button("Redraw",use_container_width=True)

    with st.form(key="seg"):
        st.markdown('<div class="controls-container">SEGMENTATION CONTROLS</div>', unsafe_allow_html=True)
        st.markdown(" ")
        col1, col2 = st.columns(2)
        if uploaded_image and submit_image:
            st.session_state.dsb2 = False
            st.image(uploaded_image)
        
        with col1:
            
            prediction_iou = st.slider('Prediction IOU threshold (default=0.8)', min_value=0.0, max_value=1.0, value=0.8)
            height = st.slider("Adjust height:", 0, 100, 50)
        with col2:
            stability_score = st.slider('Stability score threshold (default=0.85)', min_value=0.0, max_value=1.0, value=0.85)
            box_nms = st.slider('Box NMS threshold (default=0.7)', min_value=0.0, max_value=1.0, value=0.7)
            
        segment_button = st.form_submit_button("Segment image", disabled=st.session_state.dsb2, use_container_width=True,help="Submit image to enable")
       
        if segment_button:
            file_path = uploaded_image.name
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
            os.remove(file_path)

if segment_button and result:
    with left_col: 
        st.image(uploaded_image, "Uploaded image") 
    with right_col: 
        st.image(result,"Segmented image")
    


        
            
        