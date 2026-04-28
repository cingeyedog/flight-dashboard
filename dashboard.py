import streamlit as st
import pandas as pd
import json
import pydeck as pdk

st.set_page_config(layout="wide")

st.title("✈️ Flight Deals Explorer")

# =====================
# LOAD DATA
# =====================

with open("safe_data.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)

if df.empty:
    st.warning("No data available")
    st.stop()

# =====================
# FILTERS
# =====================

st.sidebar.header("🔎 Filters")

origin = st.sidebar.selectbox("Origin", ["All"] + sorted(df["origin"].unique()))
max_price = st.sidebar.slider("Max Price ($)", 200, 1500, 800)

filtered = df.copy()

if origin != "All":
    filtered = filtered[filtered["origin"] == origin]

filtered = filtered[filtered["price"] <= max_price]

# =====================
# METRICS
# =====================

col1, col2, col3 = st.columns(3)

col1.metric("Routes", len(filtered))
col2.metric("Cheapest", f"${filtered['price'].min():.0f}")
col3.metric("Avg", f"${filtered['price'].mean():.0f}")

# =====================
# DEAL COLORING
# =====================

def color_conf(val):
    if val == "high":
        return [0, 200, 0]       # green
    elif val == "medium":
        return [255, 165, 0]     # orange
    else:
        return [255, 0, 0]       # red

filtered["color"] = filtered["confidence"].apply(color_conf)

# =====================
# TABLE
# =====================

st.subheader("🌍 Cheapest Destinations")

st.dataframe(filtered.sort_values("price"))

# =====================
# CHART
# =====================

st.subheader("📊 Price Comparison")

st.bar_chart(filtered.set_index("destination")["price"])

# =====================
# MAP (INTERACTIVE)
# =====================

st.subheader("🗺️ Interactive Map")

coords = {
    "LHR": (51.4700, -0.4543),
    "CDG": (49.0097, 2.5479),
    "AMS": (52.3105, 4.7683),
    "FRA": (50.0379, 8.5622),
    "MAD": (40.4983, -3.5676),
    "BCN": (41.2974, 2.0833),
    "DUB": (53.4213, -6.2701),
    "LIS": (38.7742, -9.1342),
    "ZRH": (47.4581, 8.5555),
    "VIE": (48.1103, 16.5697),
    "MXP": (45.6306, 8.7281),
    "FCO": (41.8003, 12.2389),
    "CPH": (55.6181, 12.6560),
    "ARN": (59.6519, 17.9186),
    "OSL": (60.1976, 11.1004),
    "HEL": (60.3172, 24.9633),
    "BRU": (50.9010, 4.4844),
    "PRG": (50.1008, 14.2600),
    "BUD": (47.4369, 19.2556),
    "WAW": (52.1657, 20.9671),
}

map_data = []

for _, row in filtered.iterrows():
    dest = row["destination"]
    if dest in coords:
        lat, lon = coords[dest]
        map_data.append({
            "destination": dest,
            "price": row["price"],
            "confidence": row["confidence"],
            "lat": lat,
            "lon": lon,
            "color": row["color"]
        })

map_df = pd.DataFrame(map_data)

if not map_df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=50000,
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=50,
        longitude=10,
        zoom=3.5,
        pitch=0,
    )

    tooltip = {
        "html": "<b>{destination}</b><br/>Price: ${price}<br/>Confidence: {confidence}",
        "style": {"backgroundColor": "black", "color": "white"}
    }

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    ))

# =====================
# CLICK-TO-DETAIL (SIMULATED)
# =====================

st.subheader("🔍 Explore Route")

selected_dest = st.selectbox("Select destination", filtered["destination"].unique())

route_data = filtered[filtered["destination"] == selected_dest]

st.write(route_data)

# =====================
# SEARCH
# =====================

st.subheader("🔎 Search")

search = st.text_input("Search destination")

if search:
    result = filtered[filtered["destination"].str.contains(search.upper())]
    st.dataframe(result)
