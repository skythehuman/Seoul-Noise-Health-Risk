# Seoul-Noise-Health-Risk
Prototype for visualizing traffic noise-attributed health risks across Seoul.

**[Dashboard](https://seoul-noise-health-map.streamlit.app/)**

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
