# CricIntel Fan Intelligence

Cricket fan segmentation and intelligence platform for county cricket clubs.

## Features

- **Upload & Configure** — CSV upload with hybrid schema detection, column mapping, club name/format config
- **Fan Dashboard** — 9 charts, 5 hero metrics, segment insights cards, top 20 fans table
- **Membership Intelligence** — tier breakdown, LTV analysis, renewal risk, upgrade opportunity funnel
- **Sponsorship Intelligence** — pitch score, demographic breakdown, sponsor category recommendations, PDF deck
- **Match Intelligence** — matchday revenue by format, attendance gap analysis, hospitality/corporate upsell
- **Report** — PDF report, CSV downloads, custom metrics explorer

## Scoring Engine

Five scores (0–100) computed per fan:

| Score | Key Inputs |
|---|---|
| Engagement | Email click rate, InApp click rate, Article views, App recency, Attendance |
| Commercial | Total Revenue, Purchase counts, Recency, Membership tier weight |
| Loyalty | Tenure, Membership tier, Sustained engagement, Attendance |
| Churn Risk | Days since purchase/app/email, Engagement inverse — percentile-calibrated |
| Conversion | Email + InApp open rates, Membership gap from Surrey & England tier |

**Segments:** Loyal Members · High Potential · Win Back · Dormant · Casual  
**Journey Stages:** 1 (No Membership, Low Engagement) → 5 (Surrey & England Member)

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Sample Data

```bash
python generate_sample.py   # creates cricintel_fan_sample.csv (500 rows)
```

## Deployment (Render)

Configured via `render.yaml`. Push to GitHub and connect to Render.
