import warnings

import numpy as np
import streamlit.components.v1 as components

from funcs import get_stations_nearby

warnings.filterwarnings('ignore')
import streamlit as st

from component_callbacks import register_callback
from data_utils import load_df
from map_select import map_select
from plot_weather import plot_weather_data


def map_callback():
    data = st.session_state.map
    if data is not None:
        if data.get('marker') is not None:
            st.session_state['latLng'] = data['marker'] 
        if data.get('ws') is not None:
            usaf_str = str(data['ws']['usaf'])
            wban_str = str(data['ws']['wban'])
            st.session_state['usaf'] = usaf_str
            st.session_state['wban'] = wban_str

if __name__ == '__main__':
    register_callback("map", map_callback)
    selected_station = st.sidebar.empty()
    with selected_station.container():
        st.subheader("No station selected")

    tab1, tab2 = st.tabs(["Choose weather station", "Plot"])
        

    df = load_df()
    year_msg = 'Please select a year'

    with tab1:
        usaf_colm, wban_colm = st.columns(2)

        usaf, wban = None, None

        with usaf_colm:
            input_usaf = st.text_input(label='USAF (optional)', value='', key='usaf').strip()
        if len(input_usaf) and not input_usaf.isnumeric():
            st.error('USAF must be a number')
        elif len(input_usaf):
            usaf = int(input_usaf)

        with wban_colm:    
            input_wban = st.text_input(label='WBAN (optional)', value='', key='wban').strip()
        if len(input_wban) and not input_wban.isnumeric():
            st.error('WBAN must be a number')
        elif len(input_wban):
            wban = int(input_wban)

        ws_data = None


    if usaf is not None and wban is not None:
        df_ws = df[(df['usaf'] == usaf) & (df['wban'] == wban)]
        if len(df_ws):
            ws_data = df_ws.squeeze()
            lat = ws_data['lat']
            lon = ws_data['lon']
            selected_station.empty()
            with selected_station.container():
                st.subheader(f'{ws_data["stname"]}, {ws_data["country"]}')
                for key in ['USAF', 'WBAN', 'Lat', 'Lon']:
                    f"{key}: `{ws_data[key.lower()]}`"

                st.write('Year:')
                yy = st.selectbox(label='Year', 
                                key='year',
                                label_visibility='collapsed',
                                options = [year_msg, 
                                *reversed(range(ws_data.start.year, ws_data.end.year+1))], 
                                                index = 0)
            
                
        else:
            st.error('No weather station found with the given USAF and WBAN')

    if ws_data is None:
        # Salton Sea
        lat, lon = [33.3162, -115.8069]

    if 'latLng' not in st.session_state:
        st.session_state['latLng'] = {
            'lat': lat,
            'lon': lon
        }
        
    lat = st.session_state['latLng']['lat']
    lon = st.session_state['latLng']['lon']

    nearby = get_stations_nearby(df, lat, lon, nstations=10).astype(
        {'start': 'str', 'end': 'str'}
    )
    stations = [i.to_dict() for idx, i in nearby.iterrows()]

    with tab1:
        st.markdown('**To choose a weather station from the map**')
        st.markdown('* Click on a location on the map to move the marker, or manually enter the latitude and longitude')
        st.markdown('* Click <span style="padding: 5px; border-radius: 2px; background-color:rgb(0, 123, 255); color: white">Find stations nearby</span>'
        + ' to display the 10 closest stations',
        unsafe_allow_html=True)
        st.markdown('* Click on a station to select it')

    with tab1:
        data = map_select(lat, lon, data=stations, key="map")
    
    if isinstance(data, dict) and (data.get('ws') is not None):

        ## Ensure lat and lon are the same, otherwise stop
        data_js = data['ws']
        data_py = get_stations_nearby(
            df, 
            data['for']['lat'], 
            data['for']['lon'], nstations=10)[['stname', 'lat', 'lon']]
        data_py = [i.to_dict() for _, i in data_py.iterrows()][data_js['idx']]

        lat_match = np.isclose(data_py['lat'], data_js['lat'])
        lon_match = np.isclose(data_py['lon'], data_js['lon'])

        if not (lat_match and lon_match):
            coord_name ='Latitude' if not lat_match else 'Longitude'
            print(f"{coord_name} does not match")
            print(f"{coord_name} in Python: {data_py[coord_name.lower()[:3]]}")
            print(f"{coord_name} in JS: {data_js[coord_name.lower()[:3]]}")
            print((f"Marker data | lat: {data['for']['lat']}, lon: {data['for']['lon']}"))
            st.stop()
    
    with tab2:
        if ws_data is None:
            st.error('Please select a weather station')
        elif yy == year_msg:
            st.error('Please select a year for plotting')
        else:
            with st.spinner():
                plot_weather_data(usaf=ws_data.usaf, wban=ws_data.wban, yy=yy)
