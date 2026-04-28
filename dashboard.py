import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")

st.title("✈️ Flight Deals Explorer")

with open("safe_data.json") as f:
    raw = json.load(f)

df = pd.DataFrame(raw["routes"])
usage = raw.get("usage", {"used": 0, "limit": 1})

# =====================
# USAGE
# =====================

st.subheader("📊 API Usage")

used = usage["used"]
limit = usage["limit"]
pct = used / limit

st.progress(pct)

col1, col2, col3 = st.columns(3)
col1.metric("Used", used)
col2.metric("Remaining", limit - used)
col3.metric("Usage %", f"{pct:.0%}")

# =====================
# FILTERS
# =====================

st.sidebar.header("Filters")

origin = st.sidebar.selectbox("Origin", ["All"] + sorted(df["origin"].unique()))

airlines = ["All"] + sorted([a for a in df["airline"].dropna().unique()])
airline_filter = st.sidebar.selectbox("Airline", airlines)

max_duration = st.sidebar.slider("Max Duration (mins)", 0, 1500, 800)

# 📅 Date picker
date_range = st.sidebar.date_input(
    "Travel Dates",
    []
)

filtered = df.copy()

if origin != "All":
    filtered = filtered[filtered["origin"] == origin]

if airline_filter != "All":
    filtered = filtered[filtered["airline"] == airline_filter]

filtered = filtered[filtered["duration"].fillna(9999) <= max_duration]

if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        (pd.to_datetime(filtered["outbound"]) >= pd.to_datetime(start)) &
        (pd.to_datetime(filtered["return"]) <= pd.to_datetime(end))
    ]

# =====================
# METRICS
# =====================

st.subheader("📈 Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Routes", len(filtered))
col2.metric("Cheapest", f"${filtered['price'].min():.0f}" if not filtered.empty else "-")
col3.metric("Avg", f"${filtered['price'].mean():.0f}" if not filtered.empty else "-")

# =====================
# TABLE
# =====================

st.subheader("🌍 Deals")

st.dataframe(
    filtered.sort_values("price"),
    use_container_width=True
)

# =====================
# CHART
# =====================

st.subheader("📊 Price Chart")

if not filtered.empty:
    st.bar_chart(filtered.set_index("destination")["price"])
