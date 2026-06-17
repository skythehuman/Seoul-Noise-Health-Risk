# Seoul-Noise-Health-Risk
Streamlit + Folium (Leaflet) prototype for visualizing traffic noise-attributed health risks across Seoul.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Using Your Own Data

Place your GeoJSON file at `data/seoul_grid_1km.geojson`. Each feature should have:

```json
{
  "grid_id": "G0001",
  "Lden": 65.3,
  "EBD": 425.7,
  "risk_level": "High",
  "cluster_id": 2,
  "cluster_name": "Rail & traffic-heavy residential",
  "population": 18500,
  "elderly_pop": 3200,
  "dominant_noise": "Railway"
}
```

Without real data, the app generates demo data automatically.

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → select `app.py` → Deploy

## Structure

```
├── app.py              # Main Streamlit dashboard (3 pages)
├── ebd.py              # EBD computation pipeline (RR → PAF → DALYs → EBD)
├── demo_data.py        # Demo grid data generator
├── requirements.txt
├── .streamlit/
│   └── config.toml     # Theme & server config
└── data/
    └── (your geojson)
```
