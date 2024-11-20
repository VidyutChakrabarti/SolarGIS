import pandas as pd 
import asyncio
import aiohttp
import streamlit as st

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