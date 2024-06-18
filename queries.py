from datetime import date, datetime, timedelta

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
        ["latitude","longitude"]]
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
    business_days = data[data["business day"]][columns]
    weekends = data[data["weekend"]][columns]
    distribution_pollutants = business_days[
        ["station","pollutant"]].groupby("station")
    distribution_cities = business_days[
        ["pollutant","station"]].groupby("pollutant")
    columns = ["station","pollutant"]
    business_days = business_days.groupby(columns)
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
            lambda x: datetime.strptime(x, "%Y/%m/%d %H:%M:%S").hour)
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
        "business_days": business_days,
        "weekends": weekends,
        "latest_data": latest_data}

dictionary = load_data()
STATIONS = dictionary["distribution_pollutants"].groups.keys()

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
            items = data.iloc[:,1].unique().tolist()
            if where == "distribution_pollutants":
                items = [e+" pollution" for e in items]
    return items

def get_params(region, department, city, station):
    df = dictionary["coordinates"]
    stations, size = [], None
    if station:
        stations, size = [station], 15
    elif city:
        stations, size = get_items("cities", city), 40
    elif department:
        for city in get_items("departments", department):
            stations += get_items("cities", city)
        size = 60
    elif region:
        for department in get_items("regions", region):
            for city in get_items("departments", department):
                stations += get_items("cities", city)
    else:
        data = df 
    if stations:
        data = df.loc[stations]
    return {"data": data, "size": size}

def get_data(s, p):
    '''
    Return the pandas dataframes (or None when not enough data)
    containing hourly average air concentrations of pollutant "p" 
    recorded by station "s" on both working_days and weekends.
    '''
    x, y  = dictionary["business_days"], dictionary["weekends"]
    result = []
    for data in [x, y]:
        try:
            result.append(data.get_group((s,p)))
        except:
            result.append(None)
    return result

def get_latest_data(s, p):
    values = [0]*24
    if dictionary["latest_data"]:
        df = dictionary["latest_data"].get_group(
            (s, p)).set_index("hour")
        dictionary = {str(x): 0 for x in range(24)}
        for hour in df.index:
            dictionary[str(hour)] = df.at["hour","valeur brute"]
        values = list(dictionary.values())
    return values

def get_stations(pollutant):
    return dictionary["distribution_cities"].get_group(
        pollutant)["station"].sort_values()
