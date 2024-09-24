import streamlit as st
import requests
from pymongo import MongoClient
from datetime import datetime


client = MongoClient("mongodb+srv://singhsa6:8ujeEay81oDA37ND@cluster0.ot1z9.mongodb.net")  # Replace with your connection string
db = client['solcast_data']
collection = db['solar_irradiance']


def get_data_from_db(lat, lng, start_date, end_date):
    query = {
        'geometry.coordinates.0': lng,  
        'geometry.coordinates.1': lat,  
    }
    
    data_to_display = [] 

    try:
        results = collection.find(query)
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

    for result in results:
        solar_data = result['properties']['parameter']['ALLSKY_SFC_SW_DWN']
        filtered_data = {date: value for date, value in solar_data.items() if start_date <= date <= end_date}
        
        if filtered_data:
            data_to_display.append({
                "coordinates": (lng, lat),
                "data": filtered_data
            })

    return data_to_display


def insert_db(api_data): 
    try:
        collection.insert_one(api_data)
        st.success("Data inserted successfully!")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def fetch_solar_data(lat, lng, start_date, end_date):
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": lng,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }  
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        insert_db(data)
        return get_data_from_db(lat, lng, start_date, end_date)  
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

st.title("Solar Energy Potential Prediction")

start_date = st.text_input("Enter start date (YYYYMMDD):", "20210101")
end_date = st.text_input("Enter end date (YYYYMMDD):", "20210131")



if st.button("Fetch Solar Data"):
    try:
        solar_data = get_data_from_db(21.1537, 79.0729, start_date, end_date)

        if not solar_data:  
            st.write("No data found in the database. Fetching new data from API...")
            solar_data = fetch_solar_data(21.1537, 79.0729, start_date, end_date)

        if solar_data: 
            st.write("Solar Data retrieved successfully!")
            for entry in solar_data:
                st.write(f"Coordinates: {entry['coordinates']}")
                st.json(entry['data'])  # Display the filtered data as JSON
    except Exception as e:
        st.error(f"An error occurred: {e}")
