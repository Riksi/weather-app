import subprocess
from plots import *
from windrose import *
import pandas as pd
from datetime import datetime
from funcs import *
import os
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

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
            