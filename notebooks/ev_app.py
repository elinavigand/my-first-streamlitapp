# Importing libraries
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy

st.set_page_config(page_title="Clean Energy Sources CH", # page title, displayed on the window/tab bar
                   page_icon="🍏", # favicon: icon that shows on the window/tab bar 
                   layout="wide", # use full width of the page
                   menu_items={
                       'About': "A Streamlit app to display clean energy sources and production in Switzerland"
                   })

# Load data
# Cache data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

# Energy Sources
rpp_df_raw = load_data(path="./data/raw/renewable_power_plants_CH.csv")
rpp_df = deepcopy(rpp_df_raw)

# Geo data
with open("./data/raw/georef-switzerland-kanton.geojson") as response:
    geo_data = json.load(response)

# Adjust the data
# Map kanton names from df to the kanton names from geo_data
cantons_dict = {
'TG':'Thurgau', 
'GR':'Graubünden', 
'LU':'Luzern', 
'BE':'Bern', 
'VS':'Valais',                
'BL':'Basel-Landschaft', 
'SO':'Solothurn', 
'VD':'Vaud', 
'SH':'Schaffhausen', 
'ZH':'Zürich', 
'AG':'Aargau', 
'UR':'Uri', 
'NE':'Neuchâtel', 
'TI':'Ticino', 
'SG':'St. Gallen', 
'GE':'Genève',
'GL':'Glarus', 
'JU':'Jura', 
'ZG':'Zug', 
'OW':'Obwalden', 
'FR':'Fribourg', 
'SZ':'Schwyz', 
'AR':'Appenzell Ausserrhoden', 
'AI':'Appenzell Innerrhoden', 
'NW':'Nidwalden', 
'BS':'Basel-Stadt'}

rpp_df["canton"] = rpp_df["canton"].apply(lambda x: cantons_dict[x])

# Group data by canton
rpp_agg = rpp_df.groupby("canton")["production"].sum().reset_index()

# Add title and header
st.title("Clean Energy Sources in Switzerland")
st.text("A Streamlit web app by Elina Vigand")

# Create a bar chart with energy production per canton
st.subheader("Clean Energy Production per Canton")
# Apply log transformation to the 'production' column
rpp_agg['log_production'] = np.log1p(rpp_agg['production'])

# Create a bar chart with the log-transformed data
plotly_bar = go.Figure(go.Bar(x=rpp_agg['canton'], y=rpp_agg['log_production'], text=rpp_agg['production']))

# Define a custom hovertemplate
hovertemplate = (
    "<b>%{x}</b><br>" +
    "Production: %{customdata:.2f}" +
    "<extra></extra>"
)

# Add the custom hovertemplate to the figure
plotly_bar.update_traces(customdata=rpp_agg['production'], hovertemplate=hovertemplate)

# Update layout and axis labels
plotly_bar.update_layout(yaxis_type='log')
plotly_bar.update_xaxes(title='Canton')
plotly_bar.update_yaxes(title='Energy Production (Log Scale)')
plotly_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')

# Update the layout
plotly_bar.update_layout(
    plot_bgcolor="black",
    width=1200)

plotly_bar.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(plotly_bar)


# Setting up columns
left_column, middle_column, right_column = st.columns([3, 1, 1])

# Widgets: selectbox
sources = ["All"]+sorted(pd.unique(rpp_df['energy_source_level_2']))
s = middle_column.selectbox("Choose an energy source", sources)

# Flow control and plotting
if s == "All":
    reduced_df = rpp_df
else:
    reduced_df = rpp_df[rpp_df["energy_source_level_2"] == s]

# Group data by canton
df_total_nr_sources = reduced_df.groupby(["canton"]).size().reset_index(name="count")

# Group data by canton and energy source
df_source = reduced_df.groupby(["canton", "energy_source_level_2"]).size().reset_index(name="count")

# Create a customdata list with lists for each canton
customdata = []

# Create a set of unique energy sources
unique_sources = reduced_df["energy_source_level_2"].unique()

for canton in df_total_nr_sources["canton"]:
    canton_data_dict = df_source[df_source["canton"] == canton].set_index("energy_source_level_2")["count"].to_dict()
    
    # Ensure that each canton has entries for all unique energy sources
    canton_data = {source: canton_data_dict.get(source, 0) for source in unique_sources}
    
    customdata.append(list(canton_data.values()))  # Append values as a list

# Generate the hovertemplate dynamically
hovertemplate = (
    "<b>%{location}</b><br>"
    + "Total Count: %{z}<br>"
    + "<br>Energy Types:<br>"
    + "<br>".join(
        [
            f"{source}: %{{customdata[{i}]}}"
            for i, source in enumerate(unique_sources)
        ]
    )
    + "<extra></extra>"
)

st.subheader("Energy Sources per Canton")
# Plot the choropleth map by number of energy sources
plotly_map2 = go.Figure(go.Choroplethmapbox(
    geojson=geo_data,
    locations=df_total_nr_sources["canton"],
    featureidkey="properties.kan_name",
    z=df_total_nr_sources["count"],
    colorscale="Viridis",
    hovertemplate=hovertemplate,
    customdata=customdata
))

plotly_map2.update_layout(mapbox_style="carto-positron",
                  mapbox_zoom=6, mapbox_center = {"lat": 46.8182, "lon": 8.2275})
plotly_map2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(plotly_map2)

# Widgets: checkbox (you can replace st.xx with st.sidebar.xx)
if st.checkbox("I want to see the dataset"):
    st.dataframe(data=rpp_df)