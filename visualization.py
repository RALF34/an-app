from typing import List

import numpy as np
import streamlit as st
from matplotlib import pyplot


# https://www.who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines
WHO_RECOMMENDATIONS = {
    pollutant: value for (pollutant, value) in zip(
        ["NO2","SO2","PM2.5","PM10","CO"],
        [25,40,15,45,4]
    )
}

def plot(
    values: List[List[float]],
    pollutant: str,
    comparison: str = "") -> pyplot.figure:
    '''
    Generate the graph showing average daily variation (obtained using
    average concentrations recorded at each of the 24 hours of the day, 
    stored in "values") of air concentration of "pollutant" recorded by 
    "station".
    '''
    figure, ax = pyplot.subplots()
    figure.set_size_inches(17,14)
    # Plot the data using either a continuous line (if all the 24
    # values are different from zero) or points.
    l = list(zip(
        ["Business days","Weekends","Yesterday"],
        ["dodgerblue","cyan","peru"]))
    if comparison:
        station_A, station_B, i = comparing.split()
        color = "navy" if not(int(i)) else "cadetblue"
        l = [(station_A,l[i][1]),(station_B,color)]
    A = np.unique(np.nonzero(np.array(values[0])))
    x = [str(x)+"h00" for x in range(24)]
    for i in range(len(values)):
        args, kargs = (x, values[i]), {"label": l[i][0],"c":l[i][1]}
        if i in A:
            ax.plot(*args, **kargs)
        else:
            ax.scatter(*args, **kargs)
    # Plot a line representing the highest daily average recommended
    # by the World Health Organization.
    ax.plot(
        range(24),
        [WHO_value]*24,
        color="violet",
        ls="--",
        lw=1.7,
        label="Highest recommended \naverage (WHO)")
    # Split the graph using three air concentration thresholds.
    WHO_value = WHO_RECOMMENDATIONS[pollutant]
    thresholds = [(2*x/3)*WHO_value for x in range(1,4)]
    colors = ["limegreen","orange","red","magenta"]
    j = 0
    y_min = 0
    while thresholds[j] < upper_bound:
        ax.fill_between(
            list(range(24)),
            thresholds[j],
            y2=y_min,
            color=colors[j],
            alpha=0.1)
        y_min = thresholds[j]
        j += 1
    ax.fill_between(
        list(range(24)),
        upper_bound,
        y2=y_min,
        color=colors[j],
        alpha=0.1)
    
    highest_value = max([max(x) for x in values])
    upper_bound = (
        highest_value if highest_value > (8/7)*WHO_value else
        (8/7)*WHO_value)
    ax.set_ylim(0,upper_bound)
    ax.legend(loc="upper right")
    unit = ("m" if pollutant == "CO" else "µ")+"g/m³"
    ax.set_ylabel(
        "Air"+" "*14+"\nquantity"+" "*14+
        "\nof "+pollutant+" "*14+"\n("+ unit +")"+" "*14,
        rotation="horizontal",
        size="large")
    return figure
