# ==========================================
# STREAMLIT DASHBOARD (GERMAN BESS CO-OPTIMIZATION)
# ==========================================

import plotly.express as px
import streamlit as st
from src.engine import generate_german_market_data, run_true_co_optimization

# Streamlit page configuration
st.set_page_config(
    page_title="German BESS Co-Optimization",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚡ German BESS Co-Optimization & Grid Fee Avoidance Dashboard")
st.markdown(
    "This dashboard provides real-time operational insights for EPEX"
    " Day-Ahead arbitrage, aFRR balancing, and industrial peak shaving under"
    " German market regulations."
)

# Sidebar controls for simulation parameters
st.sidebar.header("Configuration")
bess_capacity = st.sidebar.slider("BESS Capacity (MWh)", 2.0, 50.0, 10.0)
bess_power = st.sidebar.slider("Max Power (MW)", 1.0, 25.0, 5.0)
penalty_rate = st.sidebar.number_input(
    "Grid Fee Penalty Rate (€/MW)", value=150.0
)

# Run optimization pipeline using backend engine
market_df = generate_german_market_data()
results = run_true_co_optimization(
    market_df,
    capacity_mwh=bess_capacity,
    max_power_mw=bess_power,
    grid_fee_penalty_rate=penalty_rate,
)

# Main layout metrics
col1, col2, col3 = st.columns(3)
col1.metric(
    "Original Peak Load", f"{market_df['Industrial_Load_MW'].max():.2f} MW"
)
col2.metric("Optimized Net Peak", f"{results['Net_Grid_Load_MW'].max():.2f} MW")
peak_reduction = (
    market_df["Industrial_Load_MW"].max()
    - results["Net_Grid_Load_MW"].max()
)
col3.metric("Peak Reduction", f"{peak_reduction:.2f} MW")

st.markdown("---")

# Plotly interactive chart with customized legend text color
st.subheader("📊 24-Hour Dispatch & Peak Shaving Profile")

fig = px.line(
    results,
    y=[
        "Industrial_Load_MW",
        "Net_Grid_Load_MW",
        "Optimized_Discharge_MW",
    ],
    labels={"value": "Power (MW)", "Timestamp": "Time"},
    title="Industrial Load vs Net Grid Load with BESS Dispatch",
)

# Update layout to style the legend text color (black) and background box
fig.update_layout(
    legend=dict(
        font=dict(color="black", size=12),
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
    ),
    template="plotly_dark",
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

st.success(
    "Dashboard loaded and optimized successfully! Ready for full-scale"
    " deployment."
)
