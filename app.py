"""
Seoul Noise Health Risk Dashboard
==================================
Streamlit + Folium (Leaflet) prototype.

Run:  streamlit run app.py
"""

import streamlit as st
import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

from ebd import (
    compute_ebd, WHO_LDEN_THRESHOLD, DISABILITY_WEIGHT,
    ELDERLY_THRESHOLD, EBD_THRESHOLD,
)
from demo_data import load_grid_data, CLUSTER_INFO

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seoul Noise Health Dashboard",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean up default Streamlit chrome */
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.6rem !important; font-weight: 700 !important; }
    h2 { font-size: 1.2rem !important; font-weight: 600 !important; }
    h3 { font-size: 1rem !important; font-weight: 600 !important; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e5ea;
        border-radius: 10px;
        padding: 12px 16px;
    }

    /* Risk badges */
    .risk-high   { color: #dc2626; background: #fee2e2; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
    .risk-medium { color: #b45309; background: #fef3c7; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
    .risk-low    { color: #15803d; background: #dcfce7; padding: 4px 12px; border-radius: 20px; font-weight: 600; }

    /* Formula block */
    .formula-box {
        background: #f7f8fa;
        border: 1px solid #e2e5ea;
        border-radius: 10px;
        padding: 16px 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        line-height: 1.9;
    }
</style>
""", unsafe_allow_html=True)

# ── Risk color helper ────────────────────────────────────────────────
RISK_COLORS = {"High Risk": "#ef4444", "Medium Risk": "#f59e0b", "Low Risk": "#22c55e"}

def risk_badge(level: str) -> str:
    cls = f"risk-{level.lower()}"
    icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[level]
    return f'<span class="{cls}">{icon} {level} Risk</span>'


# ── Sidebar Navigation ───────────────────────────────────────────────
with st.sidebar:
    st.title("🔊 Seoul Noise Health")
    st.caption("Traffic noise-attributed IHD burden assessment")
    st.divider()

    page = st.radio(
        "Navigate",
        ["EBD Calculator", "Risk Map", "About"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Based on EU END framework & WHO 2018 guidelines")


# =====================================================================
# PAGE 1 — EBD Calculator
# =====================================================================
if page == "EBD Calculator":
    st.title("EBD Health Risk Calculator")
    st.caption(
        "Compute the Environmental Burden of Disease for traffic noise-attributed "
        "ischemic heart disease (IHD) using the EU END methodology."
    )

    # ── Pipeline diagram ─────────────────────────────────────────────
    cols = st.columns(6)
    steps = ["1. Lden", "2. RR", "3. PAF", "4. DALYs", "5. EBD", "6. Risk"]
    for col, step in zip(cols, steps):
        col.markdown(
            f"<div style='text-align:center; padding:6px; "
            f"background:#e8f0fe; border-radius:8px; "
            f"font-size:0.8rem; font-weight:600; color:#2563eb;'>"
            f"{step}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Input form ───────────────────────────────────────────────────
    with st.container():
        st.subheader("Input Parameters")

        c1, c2, c3 = st.columns(3)

        with c1:
            lden = st.slider(
                "Noise Level — Lden (dB)",
                min_value=40.0, max_value=85.0, value=65.0, step=0.5,
                help="Day-evening-night weighted sound level",
            )
            if lden > WHO_LDEN_THRESHOLD:
                st.warning(f"⚠ Exceeds WHO guideline of {WHO_LDEN_THRESHOLD} dB")
            else:
                st.success(f"✓ Below WHO guideline of {WHO_LDEN_THRESHOLD} dB")

            population = st.number_input(
                "Total Population", min_value=0, value=15000, step=500,
                help="Per 1 km grid cell",
            )

        with c2:
            elderly = st.number_input(
                "Elderly Population (65+)", min_value=0, value=2500, step=100,
                help="Used for risk classification",
            )
            mortality = st.number_input(
                "IHD Mortality Rate (per 100k)", min_value=0.0, value=28.5,
                step=0.5, format="%.1f",
            )

        with c3:
            prevalence = st.number_input(
                "IHD Prevalence Rate (per 100k)", min_value=0.0, value=420.0,
                step=10.0, format="%.0f",
            )
            rem_life = st.number_input(
                "Remaining Life Expectancy (years)", min_value=0.0, value=15.2,
                step=0.5, format="%.1f",
            )

    # ── Compute ──────────────────────────────────────────────────────
    result = compute_ebd(lden, population, elderly, mortality, prevalence, rem_life)

    st.divider()

    # ── Results ──────────────────────────────────────────────────────
    st.subheader("Results")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Relative Risk", f"{result.rr:.4f}")
    m2.metric("PAF", f"{result.paf * 100:.2f}%")
    m3.metric("YLLs", f"{result.ylls:,.1f}")
    m4.metric("YLDs", f"{result.ylds:,.1f}")
    m5.metric("DALYs", f"{result.dalys:,.1f}")

    # Final EBD + Risk
    r1, r2 = st.columns([2, 1])
    with r1:
        st.metric("Environmental Burden of Disease (EBD)", f"{result.ebd:,.1f} DALYs")
    with r2:
        st.markdown("**Health Risk Classification**")
        st.markdown(risk_badge(result.risk_level), unsafe_allow_html=True)

    # ── Sensitivity Chart ────────────────────────────────────────────
    st.divider()
    st.subheader("Sensitivity: EBD vs. Noise Level")
    st.caption("How EBD changes as Lden increases, holding other inputs constant.")

    lden_range = np.arange(45, 86, 0.5)
    ebd_values = []
    for l in lden_range:
        r = compute_ebd(l, population, elderly, mortality, prevalence, rem_life)
        ebd_values.append(r.ebd)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=lden_range, y=ebd_values,
        mode="lines", name="EBD",
        line=dict(color="#2563eb", width=2.5),
    ))
    fig.add_vline(x=WHO_LDEN_THRESHOLD, line_dash="dash",
                  line_color="#7c3aed", annotation_text="WHO 53 dB",
                  annotation_position="top left")
    fig.add_vline(x=lden, line_dash="dot", line_color="#ef4444",
                  annotation_text=f"Current: {lden} dB",
                  annotation_position="top right")
    fig.update_layout(
        xaxis_title="Lden (dB)",
        yaxis_title="EBD (DALYs)",
        height=350,
        margin=dict(l=40, r=20, t=30, b=40),
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Formula reference ────────────────────────────────────────────
    with st.expander("Formula Reference"):
        st.markdown("""
<div class="formula-box">
<b>EBD<sub>IHD</sub> = PAF × DALYs</b><br><br>
RR = exp( ln(1.08) / 10 × (L<sub>den</sub> − 53) ) &nbsp; if L<sub>den</sub> > 53 dB<br>
PAF = (RR − 1) / RR<br>
DALYs = YLLs + YLDs<br>
YLLs = Deaths × Remaining Life Expectancy<br>
YLDs = Prevalent Cases × DW (0.521)
</div>
        """, unsafe_allow_html=True)


# =====================================================================
# PAGE 2 — Risk Map
# =====================================================================
elif page == "Risk Map":
    st.title("Seoul Noise Health Risk Map")
    st.caption("Grid cells (1 km × 1 km) colored by health risk level. Click a cell for details.")

    # ── Load data ────────────────────────────────────────────────────
    @st.cache_data
    def get_grid():
        return load_grid_data()

    gdf = get_grid()

    # ── Sidebar Filters ──────────────────────────────────────────────
    with st.sidebar:
        st.subheader("Map Filters")
        risk_filter = st.multiselect(
            "Risk Level",
            options=["High Risk", "Medium Risk", "Low Risk"],
            default=["High Risk", "Medium Risk", "Low Risk"],
        )
        cluster_options = sorted(gdf["cluster_id"].unique())
        cluster_filter = st.multiselect(
            "Cluster Type",
            options=cluster_options,
            default=cluster_options,
            format_func=lambda x: CLUSTER_INFO.get(x, {}).get("name", f"Cluster {x}"),
        )

    # Apply filters
    mask = gdf["risk_level"].isin(risk_filter) & gdf["cluster_id"].isin(cluster_filter)
    filtered = gdf[mask].copy()

    # ── Summary stats ────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    total = len(gdf)
    s1.metric("Total Cells", f"{total}")
    s2.metric("🔴 High Risk", f"{(gdf['risk_level'] == 'High Risk').sum()}")
    s3.metric("🟡 Medium Risk", f"{(gdf['risk_level'] == 'Medium Risk').sum()}")
    s4.metric("🟢 Low Risk", f"{(gdf['risk_level'] == 'Low Risk').sum()}")

    # ── Build Folium Map ─────────────────────────────────────────────
    m = folium.Map(
        location=[37.5665, 126.978],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    def style_fn(feature):
        risk = feature["properties"].get("risk_level", "Low Risk")
        return {
            "fillColor": RISK_COLORS.get(risk, "#888"),
            "color": "#ffffff",
            "weight": 0.5,
            "fillOpacity": 0.55 if risk == "Medium Risk" else 0.4 if risk == "Low Risk" else 0.7,
        }

    def highlight_fn(feature):
        return {"weight": 2, "color": "#1a1d23", "fillOpacity": 0.85}

    # Add grid layer
    if len(filtered) > 0:
        geojson_data = filtered.__geo_interface__

        folium.GeoJson(
            geojson_data,
            name="Risk Grid",
            style_function=style_fn,
            highlight_function=highlight_fn,
            tooltip=folium.GeoJsonTooltip(
                fields=["grid_id", "Lden", "risk_level", "EBD", "population"],
                aliases=["Grid ID", "Lden (dB)", "Risk", "EBD (DALYs)", "Population"],
                localize=True,
                sticky=True,
                style="font-size: 0.85rem;",
            ),
            popup=folium.GeoJsonPopup(
                fields=["grid_id", "Lden", "EBD", "risk_level",
                         "population", "elderly_pop", "cluster_name", "dominant_noise"],
                aliases=["Grid ID", "Lden (dB)", "EBD (DALYs)", "Risk Level",
                          "Population", "Elderly (65+)", "Cluster", "Noise Source"],
                localize=True,
                style="font-size: 0.85rem; min-width: 260px;",
            ),
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed; bottom:30px; left:30px; z-index:9999;
                background:white; padding:12px 16px; border-radius:8px;
                border:1px solid #ddd; font-size:13px; line-height:1.8;">
      <b>Risk Level</b><br>
      <span style="color:#ef4444">■</span> High &nbsp;
      <span style="color:#f59e0b">■</span> Medium &nbsp;
      <span style="color:#22c55e">■</span> Low
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Render map
    map_data = st_folium(m, width=None, height=540, returned_objects=[])

    # ── Distribution Charts ──────────────────────────────────────────
    st.divider()
    st.subheader("Distribution Analysis")

    c1, c2 = st.columns(2)

    with c1:
        fig_risk = px.pie(
            gdf["risk_level"].value_counts().reset_index(),
            names="risk_level", values="count",
            color="risk_level",
            color_discrete_map=RISK_COLORS,
            title="Risk Level Distribution",
            hole=0.4,
        )
        fig_risk.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig_risk, use_container_width=True)

    with c2:
        fig_lden = px.histogram(
            gdf, x="Lden", nbins=30,
            color="risk_level",
            color_discrete_map=RISK_COLORS,
            title="Lden Distribution by Risk Level",
            labels={"Lden": "Lden (dB)", "count": "Grid Cells"},
        )
        fig_lden.add_vline(x=WHO_LDEN_THRESHOLD, line_dash="dash",
                           line_color="#7c3aed",
                           annotation_text="WHO 53 dB")
        fig_lden.update_layout(
            height=320, margin=dict(t=40, b=40),
            barmode="stack", template="plotly_white",
        )
        st.plotly_chart(fig_lden, use_container_width=True)

    # ── EBD vs Population scatter ────────────────────────────────────
    fig_scatter = px.scatter(
        gdf, x="population", y="EBD",
        color="risk_level",
        color_discrete_map=RISK_COLORS,
        hover_data=["grid_id", "Lden", "elderly_pop", "cluster_name"],
        title="EBD vs. Population by Risk Level",
        labels={"population": "Population", "EBD": "EBD (DALYs)"},
        opacity=0.7,
    )
    fig_scatter.update_layout(
        height=380, margin=dict(t=40, b=40),
        template="plotly_white",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# =====================================================================
# PAGE 3 — About
# =====================================================================
elif page == "About":
    st.title("About This Dashboard")

    st.markdown("""
This dashboard visualizes the health risks of traffic noise exposure across
Seoul, South Korea. It implements the **Environmental Burden of Disease (EBD)**
framework from a doctoral dissertation on machine learning-based sustainable
urban soundscape management.
    """)

    st.subheader("Methodology")
    st.markdown("""
The EBD quantifies how much of the IHD disease burden can be attributed to
traffic noise. The pipeline follows the EU Environmental Noise Directive:
    """)

    st.markdown("""
<div class="formula-box">
<b>Step 1 — Relative Risk</b><br>
RR = exp( ln(1.08) / 10 × (L<sub>den</sub> − 53) ) &nbsp; when L<sub>den</sub> > 53 dB<br>
RR = 1 &nbsp; when L<sub>den</sub> ≤ 53 dB<br><br>
<b>Step 2 — Population Attributable Fraction</b><br>
PAF = (RR − 1) / RR<br><br>
<b>Step 3 — DALYs</b><br>
YLLs = Deaths × Remaining Life Expectancy<br>
YLDs = Prevalent Cases × DW (0.521)<br>
DALYs = YLLs + YLDs<br><br>
<b>Step 4 — Environmental Burden of Disease</b><br>
EBD<sub>IHD</sub> = PAF × DALYs
</div>
    """, unsafe_allow_html=True)

    st.subheader("Risk Classification")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.error("**🔴 High Risk**\n\n65+PO ≥ 620 AND EBD ≥ 239 DALYs")
    with r2:
        st.warning("**🟡 Medium Risk**\n\nEither threshold exceeded")
    with r3:
        st.success("**🟢 Low Risk**\n\nBoth below thresholds")

    st.subheader("Urban Environment Clusters")
    cluster_df = pd.DataFrame([
        {"Cluster": v["name_ko"], 
         "Description": v["name"],
         "Dominant Noise": v["noise"]}
        for v in CLUSTER_INFO.values()
    ])
    st.dataframe(cluster_df, use_container_width=True, hide_index=True)

    st.subheader("Data Sources")
    st.markdown("""
| Data | Source | Year |
|------|--------|------|
| Noise exposure (Lden) | Road traffic noise map, Seoul (NoiseModelling) | 2021 |
| Population | Census data (1 km grid, 통계청) | 2021 |
| IHD statistics | National health statistics (국가데이터처) | 2021 |
| Urban morphology | National spatial data (환경부, 국토부) | 2021 |
    """)

    st.subheader("References")
    st.markdown("""
- WHO (2018). [Environmental Noise Guidelines for the European Region](https://www.who.int/europe/publications/i/item/9789289053563)
- EU Environmental Noise Directive (END). [Directive 2002/49/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32002L0049)
- Tobollik, M. et al. (2019). Burden of disease due to traffic noise in Germany. *International journal of environmental research and public health*, 16(13), 2304.
- Rockhill, B. et al. (1998). Use and misuse of population attributable fractions. *American journal of public health*, 88(1), 15–19.
- Im, D., et al. (2023). Updating Korean disability weights for causes of disease: adopting an add-on study method. *Journal of Preventive Medicine and Public Health*, 56(4), 291.
    """)
