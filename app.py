import plotly.express as px
import subprocess
from plots import *
from windrose import *
import pandas as pd
from datetime import datetime
from funcs import *
import os
import streamlit as st
from streamlit_folium import st_folium
import folium

def day_of_year(yy, mm, dd):
    """
    Returns the day of the year for a given date.
    """
    return datetime(year=yy, month=mm, day=dd).timetuple().tm_yday

def hour_of_year(yy, mm, dd, hh):
    """
    Returns the hour of the year for a given date.
    """
    return hh + day_of_year(yy, mm, dd) * 24


def year_input(ws_data):
    start_year = ws_data.start.year
    end_year = ws_data.end.year
    yy = st.selectbox(label='Year', 
    label_visibility='collapsed',
    options = ['Year', *reversed(range(start_year, end_year+1))], 
                    index = 0)
    return yy

def input_manual(df, usaf_default=747187, wban_default=3104):
    colm1, colm2 = st.columns(2)
    with colm1:
        usaf = st.number_input('USAF', value=usaf_default)
    with colm2:
        wban = st.number_input('WBAN', value=wban_default)
    row_orig = df[(df['usaf'] == usaf) & (df['wban'] == wban)]
    if len(row_orig) == 0:
        st.warning("No station found with usaf={} and wban={}".format(usaf, wban))
        return 
    row = row_orig.iloc[0]
    location = [row.lat, row.lon]
    m = folium.Map(location=location, zoom_start=8)
    m.add_child(folium.Marker(
        location=location,
        popup=f'Latitude: {row.lat}\nLongitude: {row.lon}',
        tooltip=row.stname
    ))
    st_folium(m, width=1000, height=500)
    st.dataframe(row_orig)
    return row


def find_station(df, lat, lon):
    """
    - for now we will just have a select or similar
    - when the position is selected, the location details will be shown
    """
    ## fetch list of nearest stations
    stations = get_stations_nearby(df, lat, lon, nstations=10).reset_index(drop=True)
    ## show dataframe
    st.dataframe(stations)
    ## show selectbox with list of station names
    colm1, _ = st.columns(2)
    with colm1:
        select_label = 'Select a station'
        options = [select_label, *list(range(len(stations)))]
        format_func = lambda x: f'{x} - ' + stations.loc[x, 'stname'] if x != select_label else select_label
        selected = st.selectbox(
            label='station', 
            label_visibility='collapsed',
            options=options,
            format_func=format_func
        )

    if selected == select_label:
        return 

    row = stations.iloc[selected]
    return row

def choose_from_map(df, lat_default=51.544, lon_default=-0.105):
    colm1, colm2 = st.columns(2)
    with colm1:
        lat = st.number_input('Latitude',  value=lat_default)

    with colm2:
        lon = st.number_input('Longitude', value=lon_default)

    m = folium.Map(location=[lat, lon], zoom_start=16)
    m.add_child(folium.ClickForMarker())
    "How to select a location on the map:"
    "1. Click on the map to select a location"
    "2. Click on the marker to get the latitude and longitude"
    "3. Double click on the marker to remove it"
    map_data = st_folium(m, width=1000, height=500)
    if map_data['last_clicked'] is not None:
        lc = map_data['last_clicked']
        lat, lon = lc['lat'], lc['lng']
        'Latitude: ', lat, 'Longitude: ', lon
        'Nearest stations'
    row = find_station(df, lat, lon)
    return row

def select_weather_station(df):
    input_type = st.radio(
        label='Weather station', 
        label_visibility='collapsed',
        options=['manual', 'map'],
        format_func=lambda x:'Input manually' if x=='manual' else 'Choose from map',
        index=0,

    )
    if input_type == 'manual':
        row = input_manual(df)
    elif input_type == 'map':
        row = choose_from_map(df)
    return row

   
def plot_weather_data(usaf, wban, yy):
    sd = yy * 10000 + 101
    ed = yy * 10000 + 1231
    data_folder = 'data'
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)
    data_inpt = f'{data_folder}/data-{usaf}-{wban}-{yy}.csv'
    if not os.path.exists(data_inpt):
        print('Saving data to', data_inpt)
        stid = '%06i-%05i'%(usaf, wban)
        command = './data_from_station_yyyymmddhhmm.py -n {stid} -i {stid} -f YYYY MM DD HR MN TEMP DEWP SPD DIR -s {sd} -e {ed} | grep -v -e "*" -e "^\\s*$" >  {data_inpt}'
        command = command.format(stid=stid, sd=sd, ed=ed, data_inpt=data_inpt)
        ## Run this command to get the data and wait for it to finish
        subprocess.run(command, shell=True)

    forg = pd.read_csv(data_inpt, header=0, sep=',')
    n = forg.shape[0]

    if n <= 1:
        st.warning(f'No data found for {yy}')
        os.remove(data_inpt)
    else:    
        yearday = np.double(n)
        yearhour = np.double(n)
        yearmmddtime = np.double(n)
        yyyy = forg['YYYY'].values
        # print(' ... yyyy [yr]  <= [yr]             ... ')
        mm = forg['MM'].values
        # print(' ... mm [month] <= [month]          ... ')
        
        hrmn = forg['HR'].values + forg['MN'].values /60.
        # print(' ... hrmn [hr]  <= [hr:mn]          ... ')
        temp = (forg['TEMP'].values -32.)*5./9.
        # print(' ... temp [oC]  <= [oF]             ... ')
        dewp = (forg['DEWP'].values -32.)*5./9.
        # print(' ... dewp [oC]  <= [oF]             ... ')
        wspd = forg['SPD'].values * 1609./3600.
        # print(' ... wspd [m/s] <= [miles per hour] ... ')
        wdir = forg['DIR'].values 
        # print(' ... wdir [o]   <= [o]              ... ')
        
        yearday = forg.apply(
            lambda x: day_of_year(x['YYYY'], x['MM'], x['DD']),
            axis=1)
        yearhour = forg.assign(hrmn=hrmn).apply(
            lambda x: hour_of_year(x['YYYY'], x['MM'], x['DD'], 
                                    x['hrmn'])
            , axis=1)
        yearmmddtime = forg.apply(
            lambda x: '%4i-%2i-%2i %2i:%2i:00'%(x['YYYY'], x['MM'], x['DD'], x['HR'], x['MN']),
            axis=1)
    
        # print(' ... yearday [day]   <= day of year   ... ')
        # print(' ... yearhour [day]  <= hour of year   ... ')
        # print(' ... yearmmddtime <= year-mm-dd time ... ')

        e_temp = wexler_hyland(temp)
        e_dewp = wexler_hyland(dewp)
        ah_temp = abs_humid(temp, e_temp)
        ah_dewp = abs_humid(dewp, e_dewp)
        rh = e_dewp/e_temp * 100

        wbt = wet_bulb_temp(temp, rh)
        e_wbt = wexler_hyland(wbt)
        ah_wbt = abs_humid(wbt, e_wbt)
        delta_ah_wbt = ah_wbt - ah_dewp

        # print(' ... e_temp ... ')
        # print(' ... e_dewp ... ')
        # print(' ... e_wbt ... ')
        # print(' ... ah_temp ... ')
        # print(' ... ah_dewp ... ')
        # print(' ... ah_wbt ... ')
        # print(' ... rh ... ')
        # print(' ... u_pad [m/s] ... ')
        # print(' ... delta_ah_wbt ( = ah_wbt - ah_dewp) ... ')

        st.subheader('Temperature')
        st.plotly_chart(plot_temperature(yearday, temp, wbt))
        st.subheader('Humidity')
        st.plotly_chart(plot_humid(yearday, rh))
        
        st.subheader("Water evaporation")
        colm, _ = st.columns([1, 1])
        with colm:
            n_orient_options = list(range(4, 362, 2))
            n_orient_input = st.selectbox(
                label="No. points for annual water evaporation plot",
                options=n_orient_options,
                index=n_orient_options.index(18)
            )
        st.plotly_chart(plot_water_evap3(
            n_orient_input, n, delta_ah_wbt, wspd, wdir, yearhour
        ))
        kaku = st.slider(
            "Choose an orientation angle (°N)", 
            min_value=0, max_value=360,
            value=20, step=5
        )

        st.plotly_chart(
            plot_water_evap2(kaku, yearday, rh, n, delta_ah_wbt, wspd, wdir, yearhour)
        )

        st.plotly_chart(
            plot_water_evap1(kaku, yearday, rh, n, delta_ah_wbt, wspd, wdir, yearhour)
        )

        st.subheader("Wind")
        st.plotly_chart(plot_wind1(wspd, wdir))
        st.plotly_chart(plot_wind2(yearday, wspd))
        st.plotly_chart(plot_wind3(yearday, wdir))

        st.subheader("Wind rose")


        windrose_df = pd.DataFrame(dict(wspd=wspd, wdir=wdir, mm=mm))
        windrose_df = windrose_df[(windrose_df.wdir <= 360) & (windrose_df.wdir > 0)].reset_index(drop=True)
        windrose_df['wdir'] = windrose_df.wdir % 360
        wr_wspd = windrose_df.wspd.values
        wr_wdir = windrose_df.wdir.values
        freq_kwargs = dict(wspd=wr_wspd, wdir=wr_wdir)


        colm1, colm2, colm3 = st.columns(3)

        with colm1:
            month = st.selectbox(
                label='Month', 
                options=[0] + sorted(windrose_df.mm.unique()),
                format_func=lambda x: 'All' if x == 0 else calendar.month_name[x],
                index=0
            )

        with colm2:
            max_speed = st.selectbox(
                label='Max wind speed (m/s)', 
                options=list(range(2, 33)), 
                index=2
            )
        with colm3:
            num_partitions = st.selectbox(label='No. partitions', options=list(range(2, 33)), index=2)

        


        if month == 0:
            wr_kwargs = freq_kwargs

        else:
            mask = windrose_df.mm == month
            wr_wspd_month = windrose_df.wspd[mask].values
            wr_wdir_month = windrose_df.wdir[mask].values
            wr_kwargs = dict(wspd=wr_wspd_month, wdir=wr_wdir_month)


        wr_kwargs = dict(
            wr_kwargs,
            max_speed=max_speed, num_partitions=num_partitions,
            month=month
        )

        st.plotly_chart(plot_line_windrose(**wr_kwargs), use_container_width=True)

        st.plotly_chart(plot_bar_windrose(**wr_kwargs), use_container_width=True)
   
        _, colm, _ = st.columns([1, 5, 1])
        with colm:
            st.pyplot(plot_wind_polar_frequency(**freq_kwargs))
        _, colm, _ = st.columns([1, 5, 1])
        with colm:
            st.pyplot(plot_hexbin(**freq_kwargs))
            
@st.cache
def load_df():
    df_file = 'isd-history_only_available.txt'
    df = pd.read_csv(df_file, header=None, names=['text'])
    df.fillna(
        value={
            'usaf': 0, 'wban': 0, 'stname': '', 'country': '', 'label': '', 'lat': 0, 'lon': 0, 'ele': 0, 'start': '', 'end': ''
        }
    )
    text = df['text']
    df['usaf'] = text.str.slice(0, 6).str.strip()
    df['wban'] = text.str.slice(7, 12).str.strip()
    df['stname'] = text.str.slice(13, 42).str.strip()
    df['country'] = text.str.slice(43, 45).str.strip()
    df['label'] = text.str.slice(51, 55).str.strip()
    df['lat'] = text.str.slice(57, 64).str.strip()
    df['lon'] = text.str.slice(65, 73).str.strip()
    df['ele'] = text.str.slice(74, 81).str.strip()
    df['start'] = (
        text.str.slice(82, 86).str.strip() + '-' + text.str.slice(86, 88).str.strip() + '-' + text.str.slice(88, 90).str.strip()
    )
    df['end'] = (
        text.str.slice(91, 95).str.strip() + '-' + text.str.slice(95, 97).str.strip() + '-' + text.str.slice(97, 99).str.strip()
    )
    df = df.drop(columns=['text'])
    # Omit lat/lon with missing values
    df = df[(df['lat'] != '') & (df['lon'] != '')].reset_index(drop=True)
    df = df.astype(
        {'lat': float, 'lon': float, 'start': 'datetime64', 'end': 'datetime64',
         'usaf': int, 'wban': int}
    )


    return df


def main():
    df = load_df()
    tab1, tab2 = st.tabs(["Choose weather station", "Plot"])
    ws_data = None

    with tab1:
        pl = st.empty()
        pl.write("Currently selected: None")
        ws_data = select_weather_station(df)

        with pl:
            if ws_data is not None:
                "Currently selected:", ws_data['stname'],'| USAF:', ws_data['usaf'], '| WBAN:', ws_data['wban']
                    
    with tab2:
        if ws_data is None:
            st.warning("Please select a weather station first")

        else:
            (ws_data['stname'],
            "| USAF: ", ws_data['usaf'], 
            "| WBAN: ", ws_data['wban'],
            "| Lat: ", ws_data['lat'],
            "| Lon: ", ws_data['lon'])
            
            yy_colm, *_ = st.columns([1, 3])
            with yy_colm:
                yy = year_input(ws_data)
            
            if yy != 'Year':
                with st.spinner():
                    plot_weather_data(
                        usaf=ws_data.usaf, wban=ws_data.wban, yy=yy
                    )
                
        

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error: ', e)
        st.stop()
