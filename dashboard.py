import streamlit as st
import pandas as pd
import json
import pydeck as pdk

# =====================
# PAGE CONFIG
# =====================

st.set_page_config(
    layout="centered",
    page_title="Flight Deals"
)

st.title("✈️ Flight Deals")

# =====================
# AIRPORT → CITY MAP
# =====================

AIRPORT_TO_CITY = {
    "LHR": "London",
    "CDG": "Paris",
    "AMS": "Amsterdam",
    "FRA": "Frankfurt",
    "MAD": "Madrid",
    "BCN": "Barcelona",
    "DUB": "Dublin",
    "LIS": "Lisbon",
    "ZRH": "Zurich",
    "VIE": "Vienna",
    "MXP": "Milan",
    "FCO": "Rome",
    "CPH": "Copenhagen",
    "ARN": "Stockholm",
    "OSL": "Oslo",
    "HEL": "Helsinki",
    "BRU": "Brussels",
    "PRG": "Prague",
    "BUD": "Budapest",
    "WAW": "Warsaw",
    "ZAG": "Zagreb"
}

# =====================
# LOAD DATA
# =====================

with open("safe_data.json") as f:
    raw = json.load(f)

routes = raw.get("routes", [])
usage = raw.get("usage", {"used": 0, "limit": 1})

df = pd.DataFrame(routes)

if df.empty:
    st.warning("No flight data yet")
    st.stop()

# =====================
# ADD CITY NAMES
# =====================

df["origin_city"] = df["origin"].map(AIRPORT_TO_CITY).fillna(df["origin"])
df["destination_city"] = df["destination"].map(AIRPORT_TO_CITY).fillna(df["destination"])

# =====================
# FORMAT DURATION
# =====================

def format_duration(minutes):
    if pd.isna(minutes):
        return "Unknown"
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h}h {m}m"

df["duration_str"] = df["duration"].apply(format_duration)

# =====================
# DEAL SCORE
# =====================

def score_deal(row):
    score = 0

    if pd.notna(row["price"]):
        if row["price"] < 500:
            score += 50
        elif row["price"] < 650:
            score += 30
        elif row["price"] < 800:
            score += 10

    if pd.notna(row["duration"]):
        if row["duration"] < 500:
            score += 20
        elif row["duration"] < 700:
            score += 10

    if score >= 60:
        return "🔥"
    elif score >= 40:
        return "💰"
    elif score >= 20:
        return "👍"
    else:
        return "😐"

df["score"] = df.apply(score_deal, axis=1)

# =====================
# API USAGE
# =====================

used = usage["used"]
limit = usage["limit"]
pct = used / limit if limit else 0

st.progress(pct)
st.caption(f"API usage: {used}/{limit} ({pct:.0%})")

# =====================
# FILTERS
# =====================

with st.expander("🔎 Filters", expanded=False):

    origin = st.selectbox(
        "Origin",
        ["All"] + sorted(df["origin_city"].unique())
    )

    airline_filter = st.selectbox(
        "Airline",
        ["All"] + sorted(df["airline"].fillna("Unknown").unique())
    )

    max_duration = st.slider("Max Duration (mins)", 0, 1500, 800)

    date_range = st.date_input("Travel Dates", [])

# =====================
# APPLY FILTERS
# =====================

filtered = df.copy()

if origin != "All":
    filtered = filtered[filtered["origin_city"] == origin]

if airline_filter != "All":
    filtered = filtered[
        filtered["airline"].fillna("Unknown") == airline_filter
    ]

filtered = filtered[
    (filtered["duration"].isna()) |
    (filtered["duration"] <= max_duration)
]

if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        (pd.to_datetime(filtered["outbound"]) >= pd.to_datetime(start)) &
        (pd.to_datetime(filtered["return"]) <= pd.to_datetime(end))
    ]

if filtered.empty:
    st.warning("No results — showing all")
    filtered = df.copy()

# =====================
# SUMMARY
# =====================

st.markdown("### 📊 Summary")

st.metric("Routes", len(filtered))

if not filtered.empty:
    st.metric("Cheapest", f"${filtered['price'].min():.0f}")
    st.metric("Average", f"${filtered['price'].mean():.0f}")

# =====================
# DEAL CARDS
# =====================

st.markdown("### 🌍 Top Deals")

top = filtered.sort_values("price").head(10)

for _, row in top.iterrows():
    st.markdown(f"""
    ---
    **{row['score']} {row['origin_city']} → {row['destination_city']}**  
    💵 ${row['price']}  
    ✈️ {row['airline'] or 'Unknown'}  
    ⏱️ {row['duration_str']}  
    📅 {row['outbound']} → {row['return']}  
    _(Airport: {row['origin']} → {row['destination']})_
    """)

# =====================
# MAP
# =====================

st.markdown("### 🗺️ Map")

coords = {
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
    "CPH": (55.61, 12.65),
    "ARN": (59.65, 17.91),
    "OSL": (60.19, 11.10),
    "HEL": (60.31, 24.96),
    "BRU": (50.90, 4.48),
    "PRG": (50.10, 14.26),
    "BUD": (47.43, 19.25),
    "WAW": (52.16, 20.96)
}

map_data = []

for _, row in top.iterrows():
    if row["destination"] in coords:
        lat, lon = coords[row["destination"]]
        map_data.append({
            "lat": lat,
            "lon": lon,
            "price": row["price"],
            "destination": row["destination_city"]
        })

map_df = pd.DataFrame(map_data)

if not map_df.empty:
    st.map(map_df)

# =====================
# CHART
# =====================

st.markdown("### 📊 Price Chart")

if not filtered.empty:
    st.bar_chart(filtered.set_index("destination_city")["price"])
