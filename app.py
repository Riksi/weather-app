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
            st.session_state['usaf'] = data['ws']['usaf']
            st.session_state['wban'] = data['ws']['wban']
            

if __name__ == '__main__':
    register_callback("map", map_callback)
    

    sidebar_subheader = st.sidebar.empty()
    sidebar_usaf_wban = st.sidebar.container()
    sidebar_extra = st.sidebar.container()
    
    sidebar_expander = st.sidebar.expander("Instructions", expanded=True)

    with sidebar_expander:
        st.markdown("If you know then USAF and WBAN, input these values, then click  <br> <span style='padding: 5px; border-radius: 3px; border: 1px solid rgba(49, 51, 63, 0.2); background: #F9F9FB'>Find stations details</span><br> to fetch additional data and view the station on the map", unsafe_allow_html=True)
        "* Alternatively select a station in the 'Choose from map' tab, and the USAF and WBAN will be filled in"
        "* Select a year to plot in the dropdown that appears after selecting a station"
        "* Then go to the 'Plot' tab to view the plots"

    sidebar_subheader.subheader("No station selected")

    tab1, tab2 = st.tabs(["Choose from map", "Plot"])

    df = load_df()
    year_msg = 'Year'

    def should_update():
        st.session_state[f'update_usaf_wban'] = True
        
    # update_usaf, update_wban = False, False
    # if st.session_state.get('usaf_updated', False):
    #     update_usaf = True
    #     st.session_state['usaf_updated'] = False

    # if st.session_state.get('wban_updated', False):
    #     update_wban = True
    #     st.session_state['wban_updated'] = False

    update_usaf_wban = False
    if st.session_state.get('update_usaf_wban', False):
        update_usaf_wban = True
        st.session_state['update_usaf_wban'] = False

    with sidebar_usaf_wban:
        usaf, wban = None, None

        
        with st.form('form'):
            
            # usaf = st.number_input(label='USAF', step=1,
            #     key='usaf',
            #     #on_change=should_update, args=('usaf',)
            #     )

            usaf = st.text_input(label='USAF',
                key='usaf',
                #on_change=should_update, args=('usaf',)
                )
    
            wban = st.number_input(label='WBAN', key='wban',
                step=1,
                # on_change=should_update, args=('wban',)
                )
            btn = st.form_submit_button(label='Find station details', on_click=should_update)

    
    ws_data = None

    # if not ((usaf == 0) and (wban == 0)):
    if not ((usaf == '') and (wban == 0)):
        # if usaf is not None and wban is not None:
        df_ws = df[(df['usaf'] == usaf) & (df['wban'] == wban)]

        if len(df_ws):
            ws_data = df_ws.squeeze()
            lat = ws_data['lat']
            lon = ws_data['lon']
            sidebar_subheader.subheader(f'{ws_data["stname"]}, {ws_data["country"]}')
            with sidebar_extra:
                for key in ['Lat', 'Lon']:
                    f"{key}: `{ws_data[key.lower()]}`"

                yy = st.selectbox(label='Year', 
                                key='year',
                                label_visibility='collapsed',
                                options = [year_msg, 
                                *reversed(range(ws_data.start.year, ws_data.end.year+1))], 
                                                index = 0)
            
                
        else:
            with sidebar_usaf_wban:
                st.error('No weather station found with the given USAF and WBAN')



    update_lat_lon = ws_data is not None and update_usaf_wban

    if not update_lat_lon:
        # Salton Sea
        lat, lon = [33.3162, -115.8069]

    if ('latLng' not in st.session_state) or update_lat_lon:
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
        with st.expander('How to select a weather station from the map', expanded=True):
            st.markdown('* Click on a location on the map to move the marker, or manually enter the latitude and longitude')
            st.markdown('* Click <span style="padding: 5px; border-radius: 2px; background-color:rgb(0, 123, 255); color: white">Find stations nearby</span>'
            + ' to display the 10 closest stations',
            unsafe_allow_html=True)
            st.markdown('* Click on a station to select it')

    with tab1:
        data = map_select(lat, lon, data=stations, update=update_lat_lon, key="map")
    
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
            plot_err_msg = ('Please select a weather station from the left')
        elif yy == year_msg:
            plot_err_msg = ('Please select a year for plotting from the left')
        else:
            st.markdown(f'<div style="font-size:10px; color: gray; text-align: right">{ws_data.usaf}-{ws_data.wban}/{yy}</div>', unsafe_allow_html=True)
            with st.spinner():
                plot_err_msg = plot_weather_data(usaf=ws_data.usaf, wban=ws_data.wban, yy=yy)

        if plot_err_msg is not None:
            st.error(plot_err_msg)
