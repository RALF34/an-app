from datetime import date, strptime, timedelta

import pandas as pd
import streamlit as st

OVERSEAS_DEPARTMENTS = [
    "GUADELOUPE",
    "GUYANE",
    "MARTINIQUE",
    "LA REUNION",
    "MAYOTTE",
    "SAINT-MARTIN"]

@st.cache_resource
def load_data():
    locations = pd.read_csv("data/location_data.csv")
    coordinates = locations.set_index("station")[
        ["Latitude","Longitude"]]
    regions = locations[
        ["region","department"]].groupby("region")
    departments = locations[
        ["department","city"]].groupby("department")
    cities = locations[
        ["city","station"]].groupby("city")
    list_of_df = []
    for x in ["A","B","C","D","E","F"]:
        list_of_df.append(pd.read_csv(f"data/dataset_{x}.csv"))
    data = pd.concat(list_of_df, ignore_index=True)
    columns = data.columns[:-1]
    working_days = data[data["working day"]][columns]
    weekends = data[data["working day"]==False][columns]
    distribution_pollutants = working_days[
        ["station","pollutant"]].groupby("station")
    distribution_cities = working_days[
        ["pollutant","station"]].groupby("pollutant")
    columns = ["station","pollutant"]
    working_days = working_days.groupby(columns)
    weekends = weekends.groupby(columns)
     
    d = date.today()-timedelta(days=1)
    url = "https://files.data.gouv.fr/lcsqa/concentrations-de"+\
    "-polluants-atmospheriques-reglementes/temps-reel/"+\
    str(d.year)+"/FR_E2_"+d.isoformat()+".csv"
    data = pd.read_csv(url, sep=";")
    # Test whether "csv" file provide some pollution data
    # (Server errors may occur, making data unavailable).
    if "validité" in data.columns:
        # Extract rows with validated data.
        data = data[data["validité"]==1]
        # Extract rows with consistent concentration value
        # (bugs during the recording process may generate 
        # negative values.)
        data = data[data["valeur brute"]>0]
        data["hour"] = data["Date de début"].apply(
            lambda x: strptime(x, "%Y/%m/%d %H:%M:%S").hour)
        data = data[["nom site","Polluant","hour","valeur brute"]]
        latest_data = data.groupby(["nom site","Polluant"])
    else:
        latest_data = None
    return {
        "coordinates": coordinates,
        "regions": regions,
        "departments": departments,
        "cities": cities,
        "distribution_pollutants": distribution_pollutants,
        "distribution_cities": distribution_cities,
        "working_days": working_days,
        "weekends": weekends,
        "latest_data": latest_data}

dictionary = load_data()
COORDINATES = dictionary["coordinates"]
STATIONS = COORDINATES.index.values

def get_items(where, group):
    '''
    Extract the data from the appropriate pandas GroupBy object 
    which are associated to group "group_name".

    Arguments:
    where -- name of the pandas GroupBy object where we want to 
             retrieve the data from.
    group -- name of the group whose data we want to extract.
    '''
    data = dictionary[where]
    items = [""]
    if group:
        if group == "REGIONS":
            items = list(data.groups.keys())
            for e in OVERSEAS_DEPARTMENTS:
                items.remove(e)
            items.append("OUTRE-MER")
        elif group == "OUTRE-MER":
                items = OVERSEAS_DEPARTMENTS
        else:
            data = data.get_group(group)
            items = data.iloc[:,1].unique()
            if where == "distribution_pollutants":
                items = [e+" pollution" for e in items]
    return items

def get_coordinates(stations):
    return dictionary["coordinates"].loc[stations]

def get_data(s, p):
    '''
    Return the pandas dataframes (or None when not enough data)
    containing hourly average air concentrations of pollutant "p" 
    recorded by station "s" on both working_days and weekends.
    '''
    x, y  = dictionary["working_days"], dictionary["weekends"]
    result = []
    for data in [x, y]:
        try:
            result.append(data.get_group((s,p)))
        except:
            result.append(None)
    return result

def get_latest_data(s, p):
    if dictionary["latest_data"]:
        df = dictionary["latest_data"].get_group(
            (s, p)).set_index("hour")
        dictionary = {str(x): 0 for x in range(24)}
        for hour in data.index:
            dictionary[str(hour)] = df.at["hour","valeur brute"]
        return list(dictionary.values())
    else:
        return None

def get_stations(pollutant):
    return dictionary["distribution_cities"].get_group(
        pollutant)["station"].sort_values()
