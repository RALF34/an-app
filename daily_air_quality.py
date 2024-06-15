from datetime import date, timedelta
from statistics import mean

import numpy as np
import streamlit as st

import queries
import visualization

with st.spinner("Loading data..."):
    _ = queries.load_data()

st.title("Daily air quality in France")
st.write('''
    ### Select your place
    Identify the air quality monitoring station whose pollution data you are interested in.
    ''')
    
s = open("data/last_update.txt", "r").read()
ending_date = date.fromisoformat(s)-timedelta(days=1)
st.session_state["current_data"] = [None, None, None, None]
    
def get_values(boundaries, comparison=False):
    y_values = [None, None]
    start, end = boundaries
    data = (
        st.session_state["current_data"][:2] if not(comparison) else
        st.session_state["current_data"][2:])
    for i, group_by in data:
        if group_by:
            # Initialize "dictionary" which will contain the average
            # concentration values (set to zero when no data are
            # available) associated to the 24 hours of the day.
            dictionary = {str(x): 0 for x in range(24)}
            for hour in group_by.groups.keys():
                # Extract only air concentration values recorded after
                # the current starting date.
                df = group_by.get_group(hour)
                dates = np.array(df["date"].to_list(), dtype="datetime64")
                values = df["value"].values
                indexes = np.where(np.logical_and(dates>=start,dates<=end))
                # Update "dictionary".
                dictionary[str(hour)] = values[indexes].mean()
            y_values[i] = list(dictionary.values())
    return y_values
    
col1, col2 = st.columns((0.4,0.6))
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
    
    station = st.selectbox("Select a station", stations, **kwargs)

kargs = queries.get_params(region, department, city, station)
col2.map(**kargs)

if station:
    if station not in queries.STATIONS:
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
            col1, col2 = st.columns((0.9,0.1))
            with col1:
                boundaries = st.slider(
                    "Set the analysis period",
                    ending_date-timedelta(days=180),
                    ending_date,
                    value=(ending_date-timedelta(days=90),ending_date),
                    format="DD/MM/YY")
                y_values = get_values(boundaries)
                if not(np.array(st.session_state["current_data"][:2]).any()):
                    st.error("No pollution data recorded during the given period.")
                else:
                    st.pyplot(visualization.plot(y_values,pollutant))
            with col2:
                latest_data = checkbox("Show values recorded yesterday")
                if latest_data: 
                    if queries.get_latest_data(station, pollutant):
                        col1.pyplot(
                            visualization.plot(
                                y_values+[queries.get_latest_data(station, pollutant)],
                                pollutant))
                    else:
                        st.error("No pollution data recorded yesterday.")
                
comparison = st.checkbox(
    "Do you want to compare this state of air pollution against others elsewhere in France?")
if comparison:
    new_station = st.selectbox(
        "Select a station",
        queries.get_stations(pollutant),
        index=None,
        placeholder="")
    if new_station:
        data = queries.get_data(new_station, pollutant)
        for i, gb in enumerate([e.groupby("hour") for e in data]):
            st.session_state["current_data"][i+2] = gb
        col1, col2 = st.columns((0.9,0.1))
        parts = ["Working day", "Weekend"]
        with col2:
            part_of_the_week = st.radio("Part of the week", parts)
        with col1:
            boundaries = st.slider(
                "Set the analysis period",
                ending_date-timedelta(days=180),
                ending_date,
                value=(ending_date-timedelta(days=90),ending_date),
                format="DD/MM/YY")
            new_y_values = get_values(boundaries, comparison=True)
            if not(np.array(st.session_state["current_data"][2:]).any()):
                st.error("No pollution data recorded during the given period.")
            else:
                i = parts.index(part_of_the_week)
                st.pyplot(
                    visualization.plot(
                        [y_values[i],new_y_values[i]],
                        pollutant,
                        comparing=" ".join(station,new_station,str(i))))
