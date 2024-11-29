import pandas as pd 
import asyncio
import aiohttp
import streamlit as st
import time
import requests
from streamlit_extras.switch_page_button import switch_page
from io import BytesIO

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
    

def fetch_from_session_storage(key, session_state_key, browsersession):
    bs = browsersession
    data = bs.getItem(key)
    if data is not None: 
        st.session_state[f"{session_state_key}"] = data
    else: 
        raise ValueError("Session key not found.")



def fetch_and_store_image(url: str, session_key: str, fallback_page: str):
    try:
        with st.spinner("Fetching segmented image..."):
            response = requests.get(url)
            response.raise_for_status()  
            st.session_state[session_key] = BytesIO(response.content)
    except Exception as e:
            st.error("Failed to fetch image from cloud.")
            with st.spinner("An error occurred while fetching your image from the cloud. Re-try segmenting"):
                time.sleep(1)
            switch_page(f'{fallback_page}')
            

def mappie(total_cost, inner_value=5000, total_label="Total cost:", inner_label="Monthly savings with Solar:"):
    html_code = f"""
    <div style="text-align: center; margin-top: 20px;">
        <div style="position: relative; width: 150px; height: 150px; margin: auto;">
            <svg style="transform: rotate(-90deg);" width="150" height="150">
                <!-- Outer base circle -->
                <circle cx="75" cy="75" r="65" stroke="dimgray" stroke-width="15" fill="none" />
                <!-- Outer progress bar -->
                <circle id="outer-progress-bar" cx="75" cy="75" r="65" 
                        stroke="cyan" stroke-width="15" fill="none" 
                        stroke-dasharray="408" stroke-dashoffset="408" 
                        style="transition: stroke-dashoffset 0.1s linear;" />
                
                <!-- Inner base circle -->
                <circle cx="75" cy="75" r="45" stroke="darkgray" stroke-width="10" fill="none" />
                <!-- Inner progress bar -->
                <circle id="inner-progress-bar" cx="75" cy="75" r="45" 
                        stroke="hotpink" stroke-width="10" fill="none" 
                        stroke-dasharray="283" stroke-dashoffset="283" 
                        style="transition: stroke-dashoffset 0.1s linear;" />
            </svg>
            
            <!-- Center text for inner percentage -->
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                        font-size: 1.1rem; color: white; font-weight: bold;" id="cost-percentage">0%</div>
        </div>

        <!-- Label and Text beneath the chart for total cost -->
        <div style="margin-top: 10px; font-size: 0.8rem; color: cyan; font-weight: bold;">
            {total_label}: <span id="total-cost-text">0</span>
        </div>

        <!-- Label and Text beneath the total cost for inner value -->
        <div style="margin-top: 5px; font-size: 0.8rem; color: hotpink; font-weight: bold;">
            {inner_label}: <span id="inner-value-text">0</span>
        </div>
    </div>
    <script>
        const totalCost = {total_cost};
        const innerValue = {inner_value};
        const duration = 7000; // Animation duration in milliseconds (slowed down)
        const frameRate = 30; // Frames per second (slowed down)
        const frameInterval = 1000 / frameRate; // Interval per frame in milliseconds
        const totalFrames = Math.ceil(duration / frameInterval);
        
        const outerIncrement = totalCost / totalFrames;
        const innerIncrement = innerValue / totalFrames;
        
        const maxOuterDashOffset = 408; // Circumference of the outer circle
        const maxInnerDashOffset = 283; // Circumference of the inner circle
        
        const outerProgressBar = document.getElementById("outer-progress-bar");
        const innerProgressBar = document.getElementById("inner-progress-bar");
        const costPercentage = document.getElementById("cost-percentage");
        const totalCostText = document.getElementById("total-cost-text");
        const innerValueText = document.getElementById("inner-value-text");
        
        let currentOuterValue = 0;
        let currentInnerValue = 0;
        let currentFrame = 0;

        function animateCost() {{
            if (currentFrame < totalFrames) {{
                currentFrame++;
                
                // Update outer circle
                currentOuterValue = Math.min(totalCost, currentOuterValue + outerIncrement);
                const outerProgress = currentOuterValue / totalCost;
                const outerOffset = maxOuterDashOffset * (1 - outerProgress);
                outerProgressBar.style.strokeDashoffset = outerOffset.toFixed(2);
                
                // Update inner circle
                currentInnerValue = Math.min(innerValue, currentInnerValue + innerIncrement);
                const innerProgress = currentInnerValue / totalCost; // Inner value as percentage of total cost
                const innerOffset = maxInnerDashOffset * (1 - innerProgress);
                innerProgressBar.style.strokeDashoffset = innerOffset.toFixed(2);
                
                // Update central percentage text
                const percentage = parseFloat(((currentInnerValue / totalCost) * 100).toFixed(1));
                costPercentage.innerHTML = `${{percentage}}%`;
                
                // Update total cost text
                totalCostText.innerHTML = `${{Math.round(currentOuterValue).toLocaleString()}}`;
                
                // Update inner value text
                innerValueText.innerHTML = `${{Math.round(currentInnerValue).toLocaleString()}}`;
                
                // Continue animation
                requestAnimationFrame(animateCost);
            }}
        }}
        
        requestAnimationFrame(animateCost);
    </script>
    <style>
        #outer-progress-bar, #inner-progress-bar {{
            stroke-linecap: butt; /* Smooth edges for both progress bars */
            transition: stroke-dashoffset 0.1s linear;
        }}
        svg circle {{
            stroke-linecap: butt; /* Smooth edges for base circles */
        }}
    </style>
    """
    with st.container(border=True):
        st.components.v1.html(html_code, height=250)