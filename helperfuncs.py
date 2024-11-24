import pandas as pd 
import asyncio
import aiohttp
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import json
import time
import os
import tempfile
import requests
from PIL import Image
from io import BytesIO
import shutil
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

def alter_df(df):
        
    if 'rect_height' not in df.columns or 'line_height' not in df.columns:
        return pd.DataFrame()
    
    df['estimated_height'] = df['rect_height'] / df['line_height']
    
    return df

def combine_dataframes(dfs):
    combined_data = {
        'latitudes': [],
        'longitudes': [],
        'estimated_height': []
    }

    for df in dfs:
        for _, row in df.iterrows():
            coords = row['bbox_coords']  
            latitudes = [coord[1] for polygon in coords for coord in polygon]  
            longitudes = [coord[0] for polygon in coords for coord in polygon] 
            
            combined_data['latitudes'].append(latitudes)
            combined_data['longitudes'].append(longitudes)
            combined_data['estimated_height'].append(row['estimated_height'])

    combined_df = pd.DataFrame(combined_data)
    return combined_df

async def fetch_data(session, url, headers):
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def main_fetch(latitude, longitude, api_key, npanels):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    url_radiation = f'https://api.solcast.com.au/world_radiation/estimated_actuals?latitude={latitude}&longitude={longitude}&hours=24&period=PT60M'
    url_pv_power = f'https://api.solcast.com.au/world_pv_power/estimated_actuals?latitude={latitude}&longitude={longitude}&capacity=5&tilt=30&azimuth=0&hours=24&period=PT60M'
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_data(session, url_radiation, headers),
            fetch_data(session, url_pv_power, headers)
        ]
        response_radiation, response_pv_power = await asyncio.gather(*tasks)
        
        if "estimated_actuals" in response_pv_power:
            for entry in response_pv_power["estimated_actuals"]:
                entry["pv_estimate"] = float(entry["pv_estimate"])*npanels
        
        return response_radiation, response_pv_power
    

def fetch_from_session_storage(key, session_state_key, uid = 1):
    #placeholder = st.empty()
    while key not in st.session_state:
        #with placeholder:
        data = streamlit_js_eval(
            js_expressions=f"sessionStorage.getItem('{key}');",
            key=f"retrieve_{key}_{uid}",
            use_return=True
        )
        time.sleep(0.1) 
        if data:
            st.session_state[session_state_key] = json.loads(data)
            break
    #placeholder.empty()

def cleanup_temp_dir():
    temp_dir = "segimgs"
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)  # Removes all files and subdirectories
            os.makedirs(temp_dir, exist_ok=True)  # Optionally recreate the directory
        except Exception as e:
            st.error(f"Error while cleaning up the directory: {e}")


def load_image_to_tempfile(url):
    temp_dir = "segimgs"
    response = requests.get(url)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(dir=temp_dir, delete=False, suffix=".png")
        image = Image.open(BytesIO(response.content))
        image.save(temp_file.name)
        temp_file.close()
        return temp_file.name
    else:
        st.error("Failed to fetch the image.")
        return None
    

def yearly_estimate():
    outer_percentage = 100  
    inner_percentage = 72  
    fig, ax = plt.subplots(figsize=(3, 3))
    fig.patch.set_facecolor('#1E1E1E')  
    ax.set_facecolor('#1E1E1E')  


    outer_colors = ['cyan']
    ax.pie(
        [outer_percentage],
        radius=1,
        colors=outer_colors,
        startangle=90,
        wedgeprops=dict(width=0.1, edgecolor='#1E1E1E')
    )

    inner_colors = ['hotpink', 'dimgray']
    ax.pie(
        [inner_percentage, 100 - inner_percentage],
        radius=0.8,
        colors=inner_colors,
        startangle=90,
        wedgeprops=dict(width=0.1, edgecolor='#1E1E1E')
    )

    circle = Circle((0, 0), 0.7, color='#1E1E1E', ec="none")
    ax.add_artist(circle)


    ax.text(0, -1.4, "Total PV Output: 31,520 kWh", color='cyan', fontsize=10, ha='center', va='center', weight='bold')
    ax.text(0, -1.7, "Re-estimated PV Output: 22,710 kWh", color='hotpink', fontsize=10, ha='center', va='center', weight='bold')


    ax.set(aspect="equal")

    with st.sidebar:
        st.write("**Yearly Energy Throughput:**")
        st.pyplot(fig)