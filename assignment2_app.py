import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geonamescache

st.title("My Country's City Report Card")
st.write("Pick a country. This app looks at its biggest cities and tells you whether ONE giant city "
         "has most of the people, or whether people are spread across many cities.")

# Step 1: load real cities (offline) and group them by country
gc = geonamescache.GeonamesCache()
countries = gc.get_countries()
cities_by_country = {}
for city in gc.get_cities().values():
    if city["population"] >= 100_000:                       # only cities with 100,000+ people
        cities_by_country.setdefault(city["countrycode"], []).append(city)

# Keep only countries that have at least 10 such cities
country_names = {}
for country_code, city_list in cities_by_country.items():
    if len(city_list) >= 10:
        country_names[countries[country_code]["name"]] = country_code

# Step 2: the student picks a country and how many cities to look at
country_name = st.selectbox("Pick a country (try YOUR country if it is on the list!)", sorted(country_names))
number_of_cities = st.slider("How many of the biggest cities should we look at?", 3, 10, 10)

# Step 3: find the biggest cities, from biggest to smallest
all_cities = cities_by_country[country_names[country_name]]
top_cities = sorted(all_cities, key=lambda city: city["population"], reverse=True)[:number_of_cities]
biggest_city = top_cities[0]
total_people = sum(city["population"] for city in top_cities)
share_of_biggest_city = 100 * biggest_city["population"] / total_people

# Step 4: draw the satellite map. Dot size = number of people. Dot colour = size of city.
city_map = folium.Map(tiles="Esri.WorldImagery")
for city in top_cities:
    if city["population"] >= 5_000_000:
        dot_colour = "red"
    elif city["population"] >= 1_000_000:
        dot_colour = "orange"
    else:
        dot_colour = "yellow"
    folium.CircleMarker([city["latitude"], city["longitude"]],
                        radius=max(4, city["population"] ** 0.5 / 250),
                        color=dot_colour, fill=True, fill_opacity=0.7,
                        tooltip=f"{city['name']}: {city['population']:,} people").add_to(city_map)
city_map.fit_bounds([[min(city["latitude"] for city in top_cities), min(city["longitude"] for city in top_cities)],
                     [max(city["latitude"] for city in top_cities), max(city["longitude"] for city in top_cities)]])

# Step 5: show the map and the bar chart side by side
map_box, chart_box = st.columns(2)
with map_box:
    st.subheader(f"Where the biggest cities of {country_name} are")
    st_folium(city_map, height=350, returned_objects=[])
    st.caption("Bigger dot = more people. Red = over 5 million people. Orange = over 1 million. Yellow = under 1 million.")
with chart_box:
    st.subheader("How many people live in each city")
    chart_data = pd.DataFrame({"City": [city["name"] for city in top_cities],
                               "People living there": [city["population"] for city in top_cities]})
    st.bar_chart(chart_data, x="City", y="People living there", x_label="City", y_label="People living there")

# Step 6: the report card
st.subheader("Report card")
first, second, third = st.columns(3)
first.metric("Biggest city", biggest_city["name"])
second.metric("People living there", f"{biggest_city['population']:,}")
third.metric(f"Share of the {number_of_cities} cities' people", f"{share_of_biggest_city:.0f}%")
st.caption(f"Share = people in {biggest_city['name']} divided by people in all {number_of_cities} cities shown, times 100.")

if share_of_biggest_city >= 50:
    st.warning(f"One giant city! More than half of the people in these cities live in {biggest_city['name']}.")
else:
    st.success("Balanced! No single city has more than half of the people. They are spread across many cities.")
