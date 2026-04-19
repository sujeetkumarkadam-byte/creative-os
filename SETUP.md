# Creative OS — Setup Guide

## What you need
- Python 3.10+
- A Google account (same one as your Drive)
- A GitHub account (for hosting on Streamlit Cloud)

---

## Step 1 — Create the Google Sheet

1. Go to [Google Drive](https://drive.google.com) → New → Google Sheets
2. Name the spreadsheet exactly: **Creative OS — The Solved Skin**
3. Leave it empty — the app will create all the tabs on first run

---

## Step 2 — Create a Google Cloud Service Account

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Enable these two APIs:
   - **Google Sheets API**
   - **Google Drive API**
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Give it any name (e.g. `creative-os-bot`)
6. Skip optional steps, click Done
7. Click the service account → **Keys → Add Key → Create new key → JSON**
8. Download the JSON file — this is your credential file

---

## Step 3 — Share the Sheet with the service account

1. Open the JSON file, copy the `client_email` value (looks like `xxx@project.iam.gserviceaccount.com`)
2. Open your Google Sheet → Share → paste that email → give **Editor** access

---

## Step 4 — Configure secrets.toml

1. Open `.streamlit/secrets.toml` in this folder
2. Set `spreadsheet_name` to exactly match your sheet name
3. Copy every field from the downloaded JSON into `[gcp_service_account]`

---

## Step 5 — Run locally

```bash
cd creative-os
pip install -r requirements.txt
streamlit run app.py
```

Open the app in your browser → click **Initialise Google Sheet** (run this once only — it creates all the tabs with headers).

---

## Step 6 — Deploy to Streamlit Cloud (free hosting)

1. Push this folder to a GitHub repo (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Connect your GitHub repo, set main file to `app.py`
4. Under **Advanced settings → Secrets**, paste the full contents of your `secrets.toml`
5. Click Deploy

---

## Step 7 — Connect SyncWith for Meta Ads data

SyncWith will auto-populate all performance columns (ROAS, CTR, Hook Rate, etc.) in the `Master_Asset_Registry` sheet by matching on the **Meta Ad ID** column.

1. Open your Google Sheet → Extensions → SyncWith
2. Add a new sync: **Meta Ads → Google Sheets**
3. Set the **match column** to `Meta Ad ID`
4. Map the following Meta fields to columns (column names must match exactly):

| Meta field | Sheet column |
|---|---|
| ROAS | ROAS |
| Spend | Amount Spent |
| Revenue | Revenue |
| CTR (Link) | CTR |
| CPC | CPC |
| Add To Cart Rate | ATC Rate |
| Purchase Rate | CVR |
| Average Order Value | AOV |
| Hook Rate (3s video views / impressions) | Hook Rate |
| Hold Rate (ThruPlays / 3s views) | Hold Rate |
| Cost Per Purchase | CAC |

5. Set up three syncs with different date ranges: All Time, Last 30 Days (→ L30 columns), Last 7 Days (→ L7 columns)
6. Schedule each sync to run daily

Once a Meta Ad ID is added to an asset row, SyncWith will fill in performance data automatically overnight.

---

## Folder structure

```
creative-os/
├── app.py                    ← Home page
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml          ← NEVER commit this
├── utils/
│   ├── taxonomy.py           ← All dropdown values
│   └── sheets.py             ← Google Sheets read/write
└── pages/
    ├── 1_Log_Asset.py        ← Main data entry form
    ├── 2_Weekly_Dashboard.py ← Monday meeting view
    ├── 3_Asset_Registry.py   ← Full filterable table
    ├── 4_Experiment_Log.py   ← Plan & track tests
    └── 5_Source_Library.py   ← Consumer interview tracking
```
