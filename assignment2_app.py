import random
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geonamescache

st.title("Random Country Duel: Who Has ONE Giant City?")
st.write("Press the button to get two random countries. Look at their maps, make a guess, then see the data! "
         "**Share** = people in the biggest city divided by people in all 10 biggest cities, times 100.")

# Step 1: load real cities (offline) and keep the 10 biggest cities of every country that has at least 10
gc = geonamescache.GeonamesCache()
countries = gc.get_countries()
cities_by_country = {}
for city in gc.get_cities().values():
    if city["population"] >= 100_000:                       # only cities with 100,000+ people
        cities_by_country.setdefault(city["countrycode"], []).append(city)

top_cities = {}                                             # country name -> its 10 biggest cities
for country_code, city_list in cities_by_country.items():
    if len(city_list) >= 10:
        top_cities[countries[country_code]["name"]] = sorted(city_list, key=lambda city: city["population"], reverse=True)[:10]

# Step 2: the button picks two random countries and remembers them
if st.button("Pick two random countries"):
    st.session_state.pair = random.sample(sorted(top_cities), 2)
if "pair" not in st.session_state:
    st.info("Press the button to start!")
    st.stop()                                               # wait for the first random pair
country_a, country_b = st.session_state.pair
st.header(f"{country_a} vs {country_b}")

def share_of_biggest(country):
    people = [city["population"] for city in top_cities[country]]
    return 100 * people[0] / sum(people)

# Step 3: show ONLY the maps (no numbers on hover!)
for box, country in zip(st.columns(2), [country_a, country_b]):
    country_map = folium.Map(tiles="Esri.WorldImagery")
    for city in top_cities[country]:
        dot_colour = "red" if city["population"] >= 5_000_000 else "orange" if city["population"] >= 1_000_000 else "yellow"
        folium.CircleMarker([city["latitude"], city["longitude"]], radius=max(4, city["population"] ** 0.5 / 250),
                            color=dot_colour, fill=True, fill_opacity=0.7).add_to(country_map)
    country_map.fit_bounds(country_map.get_bounds())        # zoom the map to fit all 10 dots
    with box:
        st.subheader(country)
        st_folium(country_map, height=300, key=country, returned_objects=[], use_container_width=True)
st.caption("Each dot is one of the 10 biggest cities. Bigger dot = more people. Red = over 5 million, orange = over 1 million, yellow = under 1 million.")

# Step 4: guess first, then reveal
guess = st.radio("Your guess: which country has ONE giant city with the bigger share of the people?",
                 [country_a, country_b], index=None, key=f"{country_a} vs {country_b}")
if guess is None:
    st.stop()                                               # wait for the guess
winner = max([country_a, country_b], key=share_of_biggest)
if guess == winner:
    st.success(f"You were right! {winner} has the bigger giant city.")
else:
    st.error(f"Surprise! It is {winner}. Look at the numbers below.")

# Step 5: reveal the numbers and a bar chart for each country
for box, country in zip(st.columns(2), [country_a, country_b]):
    cities = top_cities[country]
    box.metric(f"{country}: biggest city", cities[0]["name"])
    box.metric(f"Share of the 10 cities' people living in {cities[0]['name']}", f"{share_of_biggest(country):.0f}%")
    box.write(f"**{country}: how many people live in each of its 10 biggest cities**")
    box.bar_chart(pd.DataFrame({"City": [city["name"] for city in cities], "People living there": [city["population"] for city in cities]}),
                  x="City", y="People living there", x_label="City", y_label="People living there")
st.info("Press the button again for a new pair. Can you get 5 right in a row?")
