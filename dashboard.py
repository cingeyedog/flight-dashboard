import streamlit as st
import pandas as pd
import json

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

# Debug (can remove later)
st.write("DEBUG: total raw routes:", len(df))

if df.empty:
    st.warning("⚠️ No flight data available yet")
    st.stop()

# =====================
# USAGE WIDGET
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

if pct > 0.8:
    st.error("⚠️ Approaching API limit")
elif pct > 0.5:
    st.warning("⚠️ Moderate usage")

# =====================
# FILTERS
# =====================

st.sidebar.header("🔎 Filters")

origin = st.sidebar.selectbox(
    "Origin",
    ["All"] + sorted(df["origin"].dropna().unique())
)

airlines = ["All"] + sorted(
    df["airline"].fillna("Unknown").unique()
)
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

# safer duration filter
filtered = filtered[
    (filtered["duration"].isna()) |
    (filtered["duration"] <= max_duration)
]

# date filter
if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        (pd.to_datetime(filtered["outbound"]) >= pd.to_datetime(start)) &
        (pd.to_datetime(filtered["return"]) <= pd.to_datetime(end))
    ]

# =====================
# FILTER DEBUG INFO
# =====================

st.subheader("📊 Filter Results")

col1, col2 = st.columns(2)
col1.metric("Total Routes", len(df))
col2.metric("Filtered Routes", len(filtered))

# =====================
# AUTO FALLBACK
# =====================

if filtered.empty:
    st.warning("⚠️ No results match your filters")

    with st.expander("Why this might happen"):
        st.write("""
        Possible reasons:
        - Airline filter removed all results
        - Duration limit too strict
        - Travel dates don't match available data
        """)

    st.info("🔄 Showing all available data instead")

    filtered = df.copy()

# =====================
# METRICS
# =====================

st.subheader("📈 Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Routes Shown", len(filtered))

if not filtered.empty:
    col2.metric("Cheapest", f"${filtered['price'].min():.0f}")
    col3.metric("Average", f"${filtered['price'].mean():.0f}")
else:
    col2.metric("Cheapest", "-")
    col3.metric("Average", "-")

# =====================
# DATA TABLE
# =====================

st.subheader("🌍 Flight Deals")

display_cols = [
    "origin",
    "destination",
    "price",
    "airline",
    "duration",
    "outbound",
    "return"
]

st.dataframe(
    filtered[display_cols].sort_values("price"),
    use_container_width=True
)

# =====================
# CHART
# =====================

st.subheader("📊 Price Comparison")

if not filtered.empty:
    st.bar_chart(
        filtered.set_index("destination")["price"]
    )

# =====================
# EXTRA INSIGHTS
# =====================

st.subheader("🧠 Insights")

if not filtered.empty:
    best_origin = (
        filtered.groupby("origin")["price"]
        .mean()
        .idxmin()
    )

    st.info(f"💡 Best airport for deals right now: **{best_origin}**")
