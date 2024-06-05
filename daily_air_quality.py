from datetime import date, timedelta
from statistics import mean

import numpy as np
import streamlit as st

import queries
import visualization

with st.spinner("Loading data..."):
    _ = queries.load_data()

st.title("Daily air pollution")
st.write('''
    ### Select a place in France
    Identify the air quality monitoring station whose pollution data you are interested in.
    ''')
    
s = open("data/last_update.txt", "r").read()
ending_date = date.fromisoformat(s)-timedelta(days=1)
st.session_state["current_data"] = [None, None]
st.session_state["no_data"] = True
    
def get_values(boundaries):
    y_values = [None, None]
    start, end = boundaries
    counter = 0
    for i, data in enumerate(st.session_state["current_data"]):
        if data:
            # Initialize "dictionary" which will contain the average
            # concentration values (set to zero when no data are
            # available) associated to the 24 hours of the day.
            dictionary = {str(x): 0 for x in range(24)}
            for hour in data.groups.keys():
                # Extract only air concentration values recorded after
                # the current starting date.
                df = data.get_group(hour)
                dates = np.array(df["date"].to_list(), dtype="datetime64")
                values = df["value"].values
                indexes = np.where(np.logical_and(dates>=start,dates<=end))
                # Update "dictionary".
                dictionary[str(hour)] = values[indexes].mean()
            y_values[i] = list(dictionary.values())
        else:
            counter += 1
    if counter < 2:
        st.session_state["no_data"] = False
    return y_values
    
col1, col2 = st.columns((5,1))
with col1:

    kwargs = {"index": None, "placeholder": ""}
        
    region = st.selectbox(
        "Select a French region",
        queries.get_items("regions", "REGIONS"),
        **kwargs)
    
    department = st.selectbox(
        "Select a French department",
        queries.get_items("regions", region),
        **kwargs)
            
    city = st.selectbox(
        "Select a French city",
        queries.get_items("departments", department),
        **kwargs)
            
    station = st.selectbox(
        "Select a station",
        queries.get_items("cities",city),
        **kwargs)
            
    if station:  
        if station not in queries.get_stations():
            st.write("Sorry, no data available for this station.")
        else:
            pollution = st.selectbox(
                "Select a type of pollution",
                queries.get_items(
                    "distribution_pollutants",
                    station),
                    **kwargs)
            if pollution:
                pollutant = pollution.split()[0]
                data = queries.get_data(station, pollutant)
                for i, gb in enumerate([e.groupby("hour") for e in data]):
                    st.session_state["current_data"][i] = gb
                boundaries = st.slider(
                    "Set the analysis period",
                    ending_date-timedelta(days=180),
                    ending_date,
                    value=(ending_date-timedelta(days=90),ending_date),
                    format="DD/MM/YY")
                y_values = get_values(boundaries)
                if st.session_state["no_data"]:
                    st.error("No pollution data are available for the given period.")
                else:
                    st.pyplot(
                        visualization.plot_variation(y_values,pollutant))
