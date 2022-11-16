import streamlit as st
import pandas as pd

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