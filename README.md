# Mini-project
Predicting Rooftop solar energy potential using real time solar irradiance data combined with extracted building footprints. Adjusting PV output taking into consideration partial shading originating from surrounding obstacles such as trees, buildings, etc. 

### Project Objectives:
•	Predicting the approximate power output specified number of PV modules can produce when installed on rooftops in given location while also estimating how partial shading can affect the total power generated. 
•	Building a deep learning model that can output the average solar energy potential of a day when provided with the area of rooftop, average solar irradiance in the location along with heights of objects obstructing sunlight in the specified area. 

## How to Run the App
To run the Streamlit app, open the terminal inside the folder and use the following command:

```bash
streamlit run solargis.py
```

### Library installations: 
```bash
pip install -r requirements.txt
```

#### In Python interactive console run: 
```python
ee.Authenticate()
```

Check out the open-source dataset: [Open Buildings](https://sites.research.google/open-buildings/)

#### Set up your google earth engine project: 
Visit: [FeatureCollection](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings_v3_polygons) and go to the feature collection link where you will be directed to set up your Earth Engine account. Note your project name and pass it as the project parameter within the app.py: 
```python
ee.Initialize(project = '(your project name)')
```

The details of the project are covered in this video : https://youtu.be/IiyKUs6mKco

The Final outputs after considering shadow coverage area :

![image](https://github.com/user-attachments/assets/cf058bdb-8edc-4078-8d9c-408ecd3f8a0c) <br>
![image](https://github.com/user-attachments/assets/a4c78610-5118-4c99-b307-ee799fbfd21d)  ![image](https://github.com/user-attachments/assets/42e880cc-0d79-4dff-bc5d-1f91b5cdc888)
<br>




