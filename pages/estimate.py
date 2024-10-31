import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import time
from streamlit_folium import st_folium
import folium 
from data import *
from helperfuncs import combine_dataframes
import pandas as pd

st.set_page_config(layout="wide", page_title='SolarGis', page_icon = 'solargislogo.png')
with open("est_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
if 'bbox_center' not in st.session_state: 
    st.session_state.bbox_center = [79.0729, 21.1537]
if 'segmented_images' not in st.session_state: 
    st.session_state.segmented_images = []

directions = ['North', 'West','South','East']
if len(st.session_state.segmented_images)==4:
    images=[]
    for i,img in enumerate(st.session_state.segmented_images): 
        images.append({
            'path': img, 'title': directions[i], 'desc':f'<b>AUTO OBJECT DETECTION:</b><br><br>{st.session_state.descriptions[i]}'
        })

else: 
    images = [
        {'path': 'https://i.ibb.co/V9hwsr6/image-with-boxes.png', 'title': directions[0] , 'desc': f'<b>AUTO OBJECT DETECTION:</b><br><br>{desc[0]}'},
        {'path': 'https://i.ibb.co/f9VLsQg/image-with-boxes.png', 'title': directions[1], 'desc': f'<b>AUTO OBJECT DETECTION:</b><br><br>{desc[1]}'},
        {'path': 'https://i.ibb.co/fknc8Nb/image-with-boxes.png', 'title': directions[2], 'desc': f'<b>AUTO OBJECT DETECTION:</b><br><br>{desc[2]}'},
        {'path': 'https://i.ibb.co/j6pY66r/image-with-boxes.png', 'title': directions[3], 'desc': f'<b>AUTO OBJECT DETECTION:</b><br><br>{desc[3]}'},      
    ]


st.sidebar.markdown('<h1 class="gradient-text">Partial Shading Re-estimation</h1>', unsafe_allow_html=True)

if st.sidebar.button("Go to Main Page", use_container_width=True):
    switch_page('main')
if st.sidebar.button("Previous", use_container_width=True):
    switch_page('app')

st.sidebar.write("Your selected bounding box:")
m = folium.Map(location=[st.session_state.bbox_center[1], st.session_state.bbox_center[0]], zoom_start=14)
folium.Marker([st.session_state.bbox_center[1], st.session_state.bbox_center[0]], popup="Location").add_to(m)
with st.sidebar:
    st_folium(m, width=300, height=200)

def preload_cards(images):
    cards = []
    for index, imag in enumerate(images):
        card_html = f"""
        <div class="card card-{index}">
            <img src="{imag['path']}" class = 'img-container'>
            <p style="font-size: 1.6em; margin-bottom: 0px;">{imag['title']}</p>
            <hr style="border: 1px solid white; margin-top: 0px; margin-bottom: 4px;">
            <div style="border-left: 1px solid white;border-right: 1px solid white;border-bottom: 1px solid white; padding: 10px;">
                <p>{imag['desc']}</p>
            </div>   
        </div>
        """
        cards.append(card_html)
    return cards

if 'cards' not in st.session_state:
    st.session_state.cards = preload_cards(images)

if 'start_index' not in st.session_state:
    st.session_state.start_index = 0

if 'animation_class' not in st.session_state:
    st.session_state.animation_class = [""] * len(st.session_state.cards)

if 'direction' not in st.session_state:
    st.session_state.direction = ''

if 'combined_df' not in st.session_state: 
    st.session_state.combined_df = None

def update_animation_classes(direction):
    
    if direction == 'left':
        st.session_state.animation_class = ["card-slide-left"] * len(st.session_state.cards)
        st.session_state.animation_class[(st.session_state.start_index)] = 'card-slide-out-to-left'
        st.session_state.animation_class[(st.session_state.start_index + 3) % len(st.session_state.cards)] = 'card-slide-in-from-right'
        #print((st.session_state.start_index),(st.session_state.start_index + 3) % len(st.session_state.cards))
    elif direction == 'right':
        st.session_state.animation_class = ["card-slide-right"] * len(st.session_state.cards)
        st.session_state.animation_class[(st.session_state.start_index+len(st.session_state.cards)-1) % len(st.session_state.cards)] = 'card-slide-in-from-left'
        st.session_state.animation_class[(st.session_state.start_index+2)% len(st.session_state.cards)] = 'card-slide-out-to-right'
        #print((st.session_state.start_index + 3) % len(st.session_state.cards),(st.session_state.start_index+2)% len(st.session_state.cards))

col1, col2= st.columns([1,1])
with col1:
    left = st.button('◀ Shift left', use_container_width=True)
    if left:
        update_animation_classes('left')
        st.session_state.direction = 'left'

with col2:
    right = st.button('Shift Right ▶', use_container_width=True)
    if right:
        update_animation_classes('right')
        st.session_state.start_index = (st.session_state.start_index) % len(st.session_state.cards)
        st.session_state.direction = 'right'

if st.session_state.direction == 'left':
    cols = st.columns(3)
    placeholders = [col.empty() for col in cols]
    
    for i in range(3):
        card_index = (st.session_state.start_index + i) % len(st.session_state.cards)
        card_class = st.session_state.animation_class[card_index]
        placeholders[i].markdown(f'<div class="{card_class}">{st.session_state.cards[card_index]}</div>', unsafe_allow_html=True)
    time.sleep(0.5)
    
    st.session_state.start_index = (st.session_state.start_index + 1) % len(st.session_state.cards)
    
    for i in range(3):
        card_index = (st.session_state.start_index + i) % len(st.session_state.cards)
        card_class = st.session_state.animation_class[card_index]
        if card_class == "card-slide-left":
            card_class = ""
        placeholders[i].markdown(f'<div class="{card_class}">{st.session_state.cards[card_index]}</div>', unsafe_allow_html=True)
    st.session_state.direction = ''
    st.session_state.animation_class = [""] * len(st.session_state.cards)
    

elif st.session_state.direction == 'right':
    cols = st.columns(3)
    placeholders = [col.empty() for col in cols]
    
    for i in range(3):
        card_index = (st.session_state.start_index + i) % len(st.session_state.cards)
        card_class = st.session_state.animation_class[card_index]
        placeholders[i].markdown(f'<div class="{card_class}">{st.session_state.cards[card_index]}</div>', unsafe_allow_html=True)
    time.sleep(0.5)
    
    st.session_state.start_index = (st.session_state.start_index - 1) % len(st.session_state.cards)
    
    for i in range(3):
        card_index = (st.session_state.start_index + i) % len(st.session_state.cards)
        card_class = st.session_state.animation_class[card_index]
        if card_class == "card-slide-right":
            card_class = ""
        placeholders[i].markdown(f'<div class="{card_class}">{st.session_state.cards[card_index]}</div>', unsafe_allow_html=True)
    st.session_state.direction = ''
    st.session_state.animation_class = [""] * len(st.session_state.cards)
    
else:
    cols = st.columns(3)
    for i in range(3):
        card_index = (st.session_state.start_index + i) % len(st.session_state.cards)
        card_class = st.session_state.animation_class[card_index]
        with cols[i]:
            st.markdown(f'<div class="{card_class}">{st.session_state.cards[card_index]}</div>', unsafe_allow_html=True)

st.divider()
with st.form(key = 'df'):
    st.write("**Manually selected objects and their estimated heights.** (Double click on cells for editing the dataframes)") 
    expand = st.expander("Explainations") 
    expand.write("▶ The heights & widths of the objects will be used to calculate the total shadow area that could be casted by an obstacle.")
    expand.write("▶ Based upon the direction in which the object is situated respective to the site in consideration, we adjust the shadow dimensions automatically and recalculate total pv output based on partial shading.")
    c1, c2 = st.columns([1,1])  
    with c1:      
        st.write("North:")
        st.session_state.dt1 = st.data_editor(st.session_state.dt1)
        st.write("West:")
        st.session_state.dt2 = st.data_editor(st.session_state.dt2)
    with c2:  
        st.write("South:")
        st.session_state.dt3 = st.data_editor(st.session_state.dt3)
        st.write("East:")
        st.session_state.dt4 = st.data_editor(st.session_state.dt4)
    re_estimate = st.form_submit_button("Re-Estimate Solar prediction", use_container_width=True)
    
    if re_estimate:
        st.session_state.bbox_coords = [[st.session_state.bbox_coords]]
        main_df = pd.DataFrame({'bbox_coords': st.session_state.bbox_coords, 'rect_height': 230, 'line_height': 46, 'estimated_height': 0})
        st.session_state.combined_df = combine_dataframes([main_df, st.session_state.dt1, st.session_state.dt2, st.session_state.dt3, st.session_state.dt4])
        switch_page('final')




