"""
Name: Nika Hakobyan
CS230:Section 3
Data:  New England Airports
URL:

Description: This is an interactive dashboard to explore airports across six New England
states (MA, CT, RI, NH, VT, ME). I use pandas for data analysis,
matplotlib and plotly for visualizations (charts), and pydeck for mapping.

"""

import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import streamlit as st
import plotly.express as px

# [ST4] Page config
st.set_page_config(page_title="New England Airports Dashboard", layout="wide")

# Title and instructions
st.title("🛩️ New England Airports Dashboard")
st.markdown("""
This dashboard allows you to explore all airports across six New England states.
- Use the sidebar filters to choose states, airport types, and scheduled service.
- Hover over dots on the map to view airport details.
- Review charts to explore the distribution and elevation of airports.
""")

# [DA1] Load & clean data
@st.cache_data
def load_data():
    df = pd.read_csv("C:/Users/hakob/OneDrive - Bentley University/PythonProject6/airports.csv")
    df = df.dropna(subset=["latitude_deg", "longitude_deg", "iso_region", "type", "elevation_ft", "name"])
    df = df[df["iso_region"].isin(["US-MA", "US-CT", "US-RI", "US-NH", "US-VT", "US-ME"])]
    return df

df = load_data()

# [DA9] Create a new derived column
df["state"] = df["iso_region"].str[-2:]

# [PY4] List comprehension
state_list = sorted({region.split("-")[1] for region in df["iso_region"]})
airport_types = sorted(df["type"].unique())

# Clean type names
type_labels = {t: t.replace("_", " ").title() for t in airport_types}
rev_type_labels = {v: k for k, v in type_labels.items()}

# [ST1], [ST2], [ST3] Sidebar Filters
with st.sidebar:
    st.markdown("### 🗺️ Filters")
    selected_states = st.multiselect("Select state(s):", state_list, default=state_list)
    selected_type_labels = st.multiselect("Select airport type(s):", list(type_labels.values()), default=list(type_labels.values()))
    st.markdown("**Scheduled Service:**")
    scheduled_option = st.radio("", ("All", "Scheduled", "Non-Scheduled"))


selected_types = [rev_type_labels[label] for label in selected_type_labels]
#[DA5]Filter Data using two or more conditions with AND
filtered_df = df[(df["state"].isin(selected_states)) & (df["type"].isin(selected_types))]

if "scheduled_service" in df.columns:
    if scheduled_option == "Scheduled":
        filtered_df = filtered_df[filtered_df["scheduled_service"] == "yes"]
    elif scheduled_option == "Non-Scheduled":
        filtered_df = filtered_df[filtered_df["scheduled_service"] == "no"]

# [DA1]Add cleaned-up label for tooltip
filtered_df["type_clean"] = filtered_df["type"].apply(lambda t: t.replace("_", " ").title())

if not filtered_df.empty:
    # [MAP] Pydeck Map
    # [PY5] Dictionary iteration
    type_colors = {
        "small_airport": [255, 0, 0],
        "medium_airport": [255, 165, 0],
        "large_airport": [0, 255, 0],
        "heliport": [128, 0, 128],
        "seaplane_base": [0, 255, 255],
        "closed": [128, 128, 128]
    }
    filtered_df["color"] = filtered_df["type"].apply(lambda x: type_colors.get(x, [200, 200, 200]))

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position="[longitude_deg, latitude_deg]",
        get_color="color",
        get_radius=800,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=filtered_df["latitude_deg"].mean(),
        longitude=filtered_df["longitude_deg"].mean(),
        zoom=6,
        pitch=0,
    )

    tooltip = {
        "html": "<b>{name}</b><br/>Type: {type_clean}<br/>Elevation: {elevation_ft} ft<br/>Location: {municipality}",
        "style": {"color": "white"}
    }

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    ))

    # [VIZ2] Highest Elevation Bar Chart [DA2] Sort in descending [DA3] Largest Values
    st.subheader("🛫 Highest Elevation Airports (Filtered)")
    top_elev = filtered_df.nlargest(10, "elevation_ft")[["name", "elevation_ft"]]
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.barh(top_elev["name"], top_elev["elevation_ft"])
    ax2.set_facecolor('#f0f0f0')
    ax2.tick_params(labelsize=9)
    ax2.set_xlabel("Elevation (ft)")
    ax2.set_title("Top 10 Highest Airports")
    st.pyplot(fig2)
else:
    st.warning("No data matches your selected filters.")

# [PY1], [PY2] Function with default parameter and returns two values
def filter_by_elevation(data, min_elev=0):
    filtered = data[data["elevation_ft"] >= min_elev]
    count = len(filtered)
    avg = filtered["elevation_ft"].mean() if count > 0 else 0
    return count, avg
# Elevation filter slider
st.sidebar.markdown("### ⛰️ Elevation Filter")
min_elevation = st.sidebar.slider("Minimum Elevation (ft):", int(df["elevation_ft"].min()), int(df["elevation_ft"].max()), 0)
elev_count, elev_avg = filter_by_elevation(df, min_elevation)

st.sidebar.markdown(f"**Airports above {min_elevation} ft:** {elev_count} total")
st.sidebar.markdown(f"**Average Elevation:** {elev_avg:.1f} ft")


# [PY3] Error Checking Try/except
try:
    if not filtered_df.empty:
        avg_elev = filtered_df["elevation_ft"].mean()
        count = len(filtered_df)
        st.sidebar.markdown(f"**Average Elevation ({', '.join(selected_states)}):** {avg_elev:.2f} ft across {count} airports")
    else:
        st.sidebar.info("No airports to summarize for this selection.")
except Exception as e:
    st.sidebar.error("Error computing average elevation")

# [PY5] Color Legend
legend_text = {
    "Red": "Small Airport",
    "Orange": "Medium Airport",
    "Green": "Large Airport",
    "Purple": "Heliport",
    "Cyan": "Seaplane Base",
    "Gray": "Closed"
}
st.sidebar.markdown("### 🧭 Map Legend")
for color, desc in legend_text.items():
    st.sidebar.markdown(f"- **{color}**: {desc}")

# [VIZ1] Pie chart of airports by state
st.subheader("🛬 Airports Per State")
state_counts = df["state"].value_counts().sort_index()
colors = ["#FF0000", "#FFA500", "#00FF00", "#800080", "#00FFFF", "#808080"]
fig3, ax3 = plt.subplots(figsize=(7, 4))
ax3.pie(
    state_counts,
    labels=state_counts.index,
    autopct="%.1f%%",
    startangle=90,
    textprops={"fontsize": 9},
    colors=colors[:len(state_counts)]
)
ax3.axis("equal")
ax3.set_title("Proportion of Airports by State")
st.pyplot(fig3)

# [VIZ3] Interactive line chart with Plotly, used website [DA4] Filter Data One condition
st.subheader("✈️ Average Airport Elevation by State")
avg_elev_by_state = df.groupby("state")["elevation_ft"].mean().sort_index().reset_index()
fig4 = px.line(
    avg_elev_by_state,
    x="state",
    y="elevation_ft",
    markers=True,
    title="Average Elevation by State",
    labels={"state": "State", "elevation_ft": "Average Elevation (ft)"}
)
st.plotly_chart(fig4, use_container_width=True)

#streamlit site says you can use emoji shortcodes or copy and paste emojis! https://blog.streamlit.io/introducing-theming/ did that for a little fun
#they also talked about config.toml which I added for customization. [ST4]