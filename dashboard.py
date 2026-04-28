import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")

st.title("✈️ Flight Deals Explorer")

# =====================
# LOAD DATA
# =====================

with open("safe_data.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)

if df.empty:
    st.warning("No data available yet")
    st.stop()

# =====================
# SIDEBAR FILTERS
# =====================

st.sidebar.header("🔎 Filters")

origins = sorted(df["origin"].unique())
selected_origin = st.sidebar.selectbox("Origin", ["All"] + origins)

max_price = st.sidebar.slider("Max Price ($)", 200, 1500, 800)

filtered_df = df.copy()

if selected_origin != "All":
    filtered_df = filtered_df[filtered_df["origin"] == selected_origin]

filtered_df = filtered_df[filtered_df["price"] <= max_price]

# =====================
# METRICS
# =====================

col1, col2, col3 = st.columns(3)

col1.metric("Routes Found", len(filtered_df))
col2.metric("Cheapest Flight", f"${filtered_df['price'].min():.0f}")
col3.metric("Average Price", f"${filtered_df['price'].mean():.0f}")

# =====================
# DEAL STRENGTH
# =====================

def deal_strength(price):
    if price < 500:
        return "🔥 Elite"
    elif price < 650:
        return "💰 Great"
    elif price < 800:
        return "👍 Good"
    else:
        return "😐 Normal"

filtered_df["deal"] = filtered_df["price"].apply(deal_strength)

# =====================
# TOP DEALS TABLE
# =====================

st.subheader("🏆 Cheapest Destinations")

top = filtered_df.sort_values("price").head(15)

st.dataframe(top)

# =====================
# BAR CHART
# =====================

st.subheader("📊 Price Comparison")

chart_df = top.set_index("destination")

st.bar_chart(chart_df["price"])

# =====================
# MAP VIEW
# =====================

st.subheader("🗺️ Map View")

AIRPORT_COORDS = {
    "LHR": (51.47, -0.45),
    "CDG": (49.01, 2.55),
    "AMS": (52.31, 4.76),
    "FRA": (50.03, 8.57),
    "MAD": (40.49, -3.56),
    "BCN": (41.30, 2.08),
    "DUB": (53.42, -6.27),
    "LIS": (38.77, -9.13),
    "ZRH": (47.45, 8.56),
    "VIE": (48.11, 16.57),
    "MXP": (45.63, 8.72),
    "FCO": (41.80, 12.25),
}

map_data = []

for _, row in top.iterrows():
    dest = row["destination"]
    if dest in AIRPORT_COORDS:
        lat, lon = AIRPORT_COORDS[dest]
        map_data.append({"lat": lat, "lon": lon})

if map_data:
    st.map(pd.DataFrame(map_data))

# =====================
# BEST ORIGIN INSIGHT
# =====================

st.subheader("🧠 Insights")

best_routes = df.sort_values("price").head(10)

best_origin = best_routes.groupby("origin")["price"].mean().idxmin()

st.info(f"💡 Best airport for deals right now: **{best_origin}**")

# =====================
# SEARCHABLE TABLE
# =====================

st.subheader("🔍 Explore All Routes")

search = st.text_input("Search destination (e.g. 'PAR', 'LON')")

if search:
    filtered_df = filtered_df[
        filtered_df["destination"].str.contains(search.upper())
    ]

st.dataframe(filtered_df.sort_values("price"))
