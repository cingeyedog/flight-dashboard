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
    raw = json.load(f)

routes = raw.get("routes", [])
usage = raw.get("usage", {"used": 0, "limit": 1})

df = pd.DataFrame(routes)

# =====================
# FORMAT DURATION
# =====================

def format_duration(minutes):
    if pd.isna(minutes):
        return "Unknown"
    hours = int(minutes) // 60
    mins = int(minutes) % 60
    return f"{hours}h {mins}m"

df["duration_str"] = df["duration"].apply(format_duration)

# =====================
# USAGE
# =====================

st.subheader("📊 API Usage")

used = usage["used"]
limit = usage["limit"]
pct = used / limit if limit else 0

col1, col2, col3 = st.columns(3)
col1.metric("Used", used)
col2.metric("Remaining", limit - used)
col3.metric("Usage %", f"{pct:.0%}")

st.progress(pct)

# =====================
# FILTERS
# =====================

st.sidebar.header("🔎 Filters")

origin = st.sidebar.selectbox(
    "Origin",
    ["All"] + sorted(df["origin"].dropna().unique())
)

airlines = ["All"] + sorted(df["airline"].fillna("Unknown").unique())
airline_filter = st.sidebar.selectbox("Airline", airlines)

max_duration = st.sidebar.slider("Max Duration (mins)", 0, 1500, 800)

date_range = st.sidebar.date_input("Travel Dates", [])

# =====================
# APPLY FILTERS
# =====================

filtered = df.copy()

if origin != "All":
    filtered = filtered[filtered["origin"] == origin]

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

# =====================
# FALLBACK
# =====================

if filtered.empty:
    st.warning("⚠️ No results match filters — showing all data")
    filtered = df.copy()

# =====================
# SUMMARY
# =====================

st.subheader("📈 Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Routes", len(filtered))
col2.metric("Cheapest", f"${filtered['price'].min():.0f}")
col3.metric("Average", f"${filtered['price'].mean():.0f}")

# =====================
# TABLE
# =====================

st.subheader("🌍 Flight Deals")

display_cols = [
    "origin",
    "destination",
    "price",
    "airline",
    "duration_str",
    "outbound",
    "return"
]

st.dataframe(
    filtered[display_cols].sort_values("price"),
    use_container_width=True
)

# =====================
# INTERACTIVE MAP
# =====================

st.subheader("🗺️ Map")

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
    if row["destination"] in coords:
        lat, lon = coords[row["destination"]]
        map_data.append({
            "lat": lat,
            "lon": lon,
            "price": row["price"],
            "destination": row["destination"]
        })

map_df = pd.DataFrame(map_data)

if not map_df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[lon, lat]',
        get_radius=50000,
        get_fill_color='[200, 30, 0, 160]',
        pickable=True
    )

    view_state = pdk.ViewState(latitude=50, longitude=10, zoom=3.5)

    tooltip = {
        "html": "<b>{destination}</b><br/>Price: ${price}"
    }

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    ))

# =====================
# ROUTE SELECTION
# =====================

st.subheader("🔍 Explore Route")

if not filtered.empty:
    selected = st.selectbox(
        "Select destination",
        filtered["destination"].unique()
    )

    route_df = filtered[filtered["destination"] == selected]

    st.write(route_df[display_cols])

# =====================
# PRICE TREND
# =====================

st.subheader("📈 Price Trend (Basic)")

# simulate trend using sorted prices
trend_df = filtered.sort_values("price")

if not trend_df.empty:
    st.line_chart(trend_df["price"])
