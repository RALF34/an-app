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

m = st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: rgb(0, 207, 0);
    border-color: rgb(0, 207, 0)
}
</style>""", unsafe_allow_html=True)
    
def get_values(boundaries, comparison=False):
    y_values = [None, None]
    start, end = boundaries
    data = st.session_state["current_data"][:2] if not(comparison) else \
    st.session_state["current_data"][2:]
    for i, group_by in enumerate(data):
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
    stations = queries.get_items("cities", city)
    selected_station = None
    if stations:
        if len(stations) > 1:
            names = [s[0] for s in stations]
            name = st.radio(
                "Select a station",
                names,
                help="The selected station appears in green on the map",
                index=None)
            selected_station = (name, stations[names.index(name)][1])
        else:
            selected_station = stations[0]

with col2:
    if (region or (region == "OUTRE MER" and department)):
        zoom = 11 if stations else None
        st.map(
            queries.get_df(
                region, department, stations, selected_station=selected_station[0]),
                color="color",
                zoom=zoom)
        
with col1:
    if selected_station:
        if selected_station[1] not in queries.STATIONS:
            st.write("Sorry, no data available for this station.")
        else:
            pollution = st.selectbox(
                "Select a type of pollution",
                queries.get_items(
                    "distribution_pollutants",
                    selected_station[1]),
                    **kwargs)
            if pollution:
                pollutant = pollution.split()[0]
                data = queries.get_data(selected_station[1], pollutant)
                for i, df in enumerate(data):
                    st.session_state["current_data"][i] = None if not(df) \
                    else df.groupby("hour")
                boundaries = st.slider(
                    "Set the analysis period",
                    ending_date-timedelta(days=180),
                    ending_date,
                    value=(ending_date-timedelta(days=90) ,ending_date),
                    format="DD/MM/YY")
                y_values = get_values(boundaries)
                if y_values == [None, None]:
                    st.error("No pollution data recorded during the given period.")
                else:
                    if None in y_values:
                        y_values[y_values.index(None)] = [0]*24
                    latest_data = st.toggle("Latest data")
                    if latest_data:
                        y_values += [queries.get_latest_data(selected_station[1], pollutant)]
                    st.pyplot(visualization.plot(y_values, pollutant))

                comparison = st.checkbox("Compare against other cities")
                if comparison:
                    df = queries.get_stations(pollutant)
                    stations = df.index.to_list()
                    options = [x[0]+" ("+x[1]+")" for x in stations]
                    new_station = st.selectbox("Select a station", options, **kwargs)
                    if new_station:
                        data = queries.get_data(
                            df.at[stations[options.index(new_station)],"code"],
                            pollutant)
                        for i, df in enumerate(data):
                            st.session_state["current_data"][i+2] = None if not(df) \
                            else df.groupby("hour")
                        boundaries = st.slider(
                            "Set the analysis period",
                            ending_date-timedelta(days=180),
                            ending_date,
                            value=(ending_date-timedelta(days=90), ending_date),
                            format="DD/MM/YY")
                        new_y_values = get_values(boundaries, comparison=True)
                        if new_y_values == [None, None]:
                            st.error("No pollution data recorded during the given period.")
                        else:
                            if None in new_y_values:
                                new_y_values[new_y_values.index(None)] = [0]*24
                            parts = ["business days", "Weekend"]
                            part_of_the_week = st.radio("", parts, horizontal=True)
                            i = parts.index(part_of_the_week)
                            st.pyplot(
                                visualization.plot(
                                    [y_values[i],new_y_values[i]],
                                    pollutant,
                                    comparison=" ".join(selected_station[0],new_station,str(i))))
