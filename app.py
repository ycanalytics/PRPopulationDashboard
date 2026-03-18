import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="YC Analytics | Puerto Rican Population Dashboard",
    layout="wide"
)

# =========================================================
# Branding Header
# =========================================================
logo_path = Path("logo.png")

col_logo, col_title = st.columns([1, 5])

with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=140)

with col_title:
    st.markdown(
        """
        <h1 style='margin-bottom:0;'>YC Analytics</h1>
        <h3 style='margin-top:0; color:#2563EB; font-weight:500;'>
            Puerto Rican Population Distribution Dashboard
        </h3>
        <p style='margin-top:0; color:#475569;'>
            Demographic analysis using Python, Plotly, and Streamlit
        </p>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================================================
# Load and Prepare Data
# =========================================================
df = pd.read_csv("puerto_rican_population.csv")

df = df.set_index("Label (Grouping)").T
df.columns = df.columns.astype(str).str.strip()

df = df.reset_index().rename(columns={"index": "State"})
df["State"] = df["State"].astype(str).str.strip()
df = df[~df["State"].str.contains("Margin of Error", na=False)].copy()

puerto_rican_col = "Puerto Rican"
if puerto_rican_col in df.columns:
    df = df[["State", puerto_rican_col]].rename(
        columns={puerto_rican_col: "Puerto_Rican_Population"}
    )
else:
    st.error(f"Column '{puerto_rican_col}' not found. Available columns: {list(df.columns)}")
    st.stop()

df = df.dropna(subset=["Puerto_Rican_Population"]).copy()
df["Puerto_Rican_Population"] = pd.to_numeric(
    df["Puerto_Rican_Population"].astype(str).str.replace(",", "", regex=False),
    errors="coerce"
)
df = df.dropna(subset=["Puerto_Rican_Population"]).copy()

df["State"] = (
    df["State"]
    .astype(str)
    .str.replace("!!Estimate", "", regex=False)
    .str.strip()
)

us_state_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "Puerto Rico": "PR"
}

df["State_Full"] = df["State"]

pr_row = df[df["State_Full"] == "Puerto Rico"].copy()
df_map = df[df["State_Full"] != "Puerto Rico"].copy()

df_map["State"] = df_map["State_Full"].map(us_state_abbrev)
df_map = df_map.dropna(subset=["State", "Puerto_Rican_Population"]).copy()
df_map = df_map.sort_values("Puerto_Rican_Population", ascending=False).reset_index(drop=True)
df_map["Rank"] = df_map.index + 1
df_map["log_population"] = np.log10(df_map["Puerto_Rican_Population"])

puerto_rico_population = int(pr_row["Puerto_Rican_Population"].iloc[0]) if not pr_row.empty else None

# =========================================================
# Sidebar Filters
# =========================================================
st.sidebar.header("Filters")

all_states = sorted(df_map["State_Full"].unique().tolist())
selected_states = st.sidebar.multiselect(
    "Select states",
    options=all_states,
    default=all_states
)

top_n = st.sidebar.slider(
    "Top N states for bar chart",
    min_value=5,
    max_value=min(20, len(df_map)),
    value=10,
    step=1
)

show_log_scale = st.sidebar.checkbox("Use log scale on map", value=True)

# Apply filters
filtered_map = df_map[df_map["State_Full"].isin(selected_states)].copy()

if filtered_map.empty:
    st.warning("No states selected. Please choose at least one state.")
    st.stop()

filtered_map = filtered_map.sort_values("Puerto_Rican_Population", ascending=False).reset_index(drop=True)
filtered_map["Rank"] = filtered_map.index + 1
filtered_map["log_population"] = np.log10(filtered_map["Puerto_Rican_Population"])

top_n_states = filtered_map.head(top_n).copy()

# =========================================================
# Metrics
# =========================================================
total_us_population = int(filtered_map["Puerto_Rican_Population"].sum())
top_state = filtered_map.iloc[0]["State_Full"]
top_state_value = int(filtered_map.iloc[0]["Puerto_Rican_Population"])

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Filtered Population Total", f"{total_us_population:,}")
metric2.metric("Top State", top_state)
metric3.metric("Top State Population", f"{top_state_value:,}")

st.markdown("")

# =========================================================
# Choropleth Map
# =========================================================
map_color_col = "log_population" if show_log_scale else "Puerto_Rican_Population"
map_label = "Population (log scale)" if show_log_scale else "Population"

fig_map = px.choropleth(
    filtered_map,
    locations="State",
    locationmode="USA-states",
    color=map_color_col,
    scope="usa",
    hover_name="State_Full",
    hover_data={
        "Puerto_Rican_Population": ":,",
        "Rank": True,
        "log_population": False,
        "State": False
    },
    color_continuous_scale="Blues",
    labels={map_color_col: map_label},
    title="Puerto Rican Population Distribution Across the United States"
)

fig_map.update_traces(
    marker_line_color="white",
    marker_line_width=0.8,
    hovertemplate="<b>%{hovertext}</b><br>Population: %{customdata[0]:,}<br>Rank: %{customdata[1]}<extra></extra>"
)

fig_map.update_layout(
    title={"x": 0.5, "xanchor": "center"},
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Arial", size=12, color="black"),
    margin=dict(l=30, r=30, t=80, b=30)
)

if puerto_rico_population is not None:
    fig_map.add_annotation(
        x=0.99,
        y=0.02,
        xref="paper",
        yref="paper",
        text=f"<b>Puerto Rico</b><br>{puerto_rico_population:,}",
        showarrow=False,
        align="right",
        bgcolor="white",
        bordercolor="lightgray",
        borderwidth=1,
        borderpad=6
    )

st.plotly_chart(fig_map, use_container_width=True)

# =========================================================
# Top N Bar Chart
# =========================================================
fig_bar = px.bar(
    top_n_states,
    x="Puerto_Rican_Population",
    y="State_Full",
    orientation="h",
    text="Puerto_Rican_Population",
    color="Puerto_Rican_Population",
    color_continuous_scale="Blues",
    labels={
        "Puerto_Rican_Population": "Population",
        "State_Full": "State"
    },
    title=f"Top {top_n} U.S. States by Puerto Rican Population"
)

fig_bar.update_traces(
    texttemplate="%{text:,}",
    textposition="outside",
    marker_line_color="white",
    marker_line_width=0.8,
    customdata=top_n_states[["Rank"]].values,
    hovertemplate="<b>%{y}</b><br>Population: %{x:,}<br>Rank: %{customdata[0]}<extra></extra>"
)

fig_bar.update_layout(
    title={"x": 0.5, "xanchor": "center"},
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Arial", size=12, color="black"),
    margin=dict(l=30, r=80, t=80, b=30),
    coloraxis_showscale=False,
    xaxis=dict(
        title="Population",
        tickformat=",",
        showgrid=True,
        gridcolor="lightgray"
    ),
    yaxis=dict(
        title="",
        categoryorder="total ascending"
    )
)

st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# Business Narrative
# =========================================================
st.markdown("## Business Context")
st.markdown(
    "This dashboard helps organizations identify where Puerto Rican populations are most concentrated "
    "across the United States, supporting demographic analysis, market targeting, service planning, "
    "and outreach strategy."
)

st.markdown("## Insights")
st.markdown(
    "The choropleth map reveals geographic distribution, while the ranked bar chart makes it easier to "
    "compare the states with the largest populations. Together, the visuals show concentration in a few "
    "major states alongside a broader national footprint."
)

st.markdown("## Conclusion")
st.markdown(
    "This project transforms raw Census-style data into a portfolio-ready analytics dashboard using "
    "Python, Pandas, Plotly, and Streamlit."
)