"""Standalone script — run once to generate cricintel_fan_sample.csv"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

PLAYERS = [
    "Rory Burns", "Jamie Overton", "Ben Foakes", "Sam Curran",
    "Jordan Clark", "Dan Worrall", "Gus Atkinson", "Oli Pope",
    "Will Jacks", "Jason Roy",
]

MEMBERSHIP_ORDER = ["None", "Associate", "Full Member", "Life Member", "Surrey & England"]

TODAY = date(2026, 5, 6)


def generate_sample_data(n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    random.seed(42)

    fan_ids = [f"FAN{i:04d}" for i in range(1, n + 1)]
    ages = np.clip(rng.normal(45, 15, n).astype(int), 6, 80)
    genders = rng.choice(["Male", "Female", "Non-binary"], n, p=[0.65, 0.25, 0.10])
    counties = rng.choice(
        ["England", "Surrey", "Kent", "Yorkshire", "Lancashire", "Middlesex", "Warwickshire", "Other"],
        n, p=[0.20, 0.25, 0.10, 0.10, 0.10, 0.10, 0.08, 0.07],
    )
    membership_cats = rng.choice(
        MEMBERSHIP_ORDER, n, p=[0.30, 0.25, 0.25, 0.12, 0.08]
    )
    fan_types = rng.choice(["Avid", "Casual", "Family", "Corporate"], n, p=[0.30, 0.35, 0.25, 0.10])
    has_app = rng.choice(["Yes", "No"], n, p=[0.55, 0.45])

    # Email
    email_campaigns = rng.integers(5, 50, n)
    open_r = rng.uniform(0.10, 0.70, n)
    click_r = open_r * rng.uniform(0.10, 0.40, n)
    email_opens = (email_campaigns * open_r).astype(int)
    email_clicks = (email_campaigns * click_r).astype(int)

    # InApp (only if HAS_APP == Yes)
    inapp_campaigns = np.where(has_app == "Yes", rng.integers(3, 30, n), 0)
    inapp_or = rng.uniform(0.20, 0.80, n)
    inapp_cr = inapp_or * rng.uniform(0.10, 0.50, n)
    inapp_opens = np.where(has_app == "Yes", (inapp_campaigns * inapp_or).astype(int), 0)
    inapp_clicks = np.where(has_app == "Yes", (inapp_campaigns * inapp_cr).astype(int), 0)

    article_views = rng.integers(0, 300, n)

    mem_mult = {"None": 0.5, "Associate": 1.0, "Full Member": 2.0, "Life Member": 3.0, "Surrey & England": 4.0}
    ticket_purchases = np.array([max(0, int(rng.normal(mem_mult[m] * 3, 2))) for m in membership_cats])
    membership_purchases = np.array([max(0, int(rng.normal(mem_mult[m] * 2, 1))) for m in membership_cats])
    retail_purchases = np.array([max(0, int(rng.normal(mem_mult[m] * 2, 2))) for m in membership_cats])

    rev_ranges = {
        "None": (0, 50), "Associate": (50, 200), "Full Member": (200, 600),
        "Life Member": (500, 1500), "Surrey & England": (1000, 3000),
    }
    total_revenues = np.array([round(rng.uniform(*rev_ranges[m]), 2) for m in membership_cats])

    # Recency offsets: higher tier = more recent (smaller offset from today)
    recency = {
        "None": (365 * 2, 365 * 3), "Associate": (180, 365 * 2),
        "Full Member": (60, 365), "Life Member": (30, 180), "Surrey & England": (0, 60),
    }
    att_ranges = {
        "None": (0, 5), "Associate": (1, 8), "Full Member": (3, 15),
        "Life Member": (5, 20), "Surrey & England": (8, 25),
    }

    first_purchase_dates, last_purchase_dates = [], []
    first_app_opens, last_app_opens = [], []
    first_email_opens, last_email_opens = [], []
    join_dates, attendance_frequencies = [], []

    for i, m in enumerate(membership_cats):
        lo, hi = recency[m]

        # Join date 2010-2024
        jd_off = random.randint(0, (date(2024, 12, 31) - date(2010, 1, 1)).days)
        join_dates.append((date(2010, 1, 1) + timedelta(days=jd_off)).isoformat())

        # First purchase 2018-2023
        fp_off = random.randint(0, (date(2023, 12, 31) - date(2018, 1, 1)).days)
        fp = date(2018, 1, 1) + timedelta(days=fp_off)
        first_purchase_dates.append(fp.isoformat())

        lp_off = random.randint(int(lo), int(hi))
        lp = TODAY - timedelta(days=lp_off)
        lp = max(lp, fp + timedelta(days=30))
        last_purchase_dates.append(lp.isoformat())

        # App dates
        if has_app[i] == "Yes":
            fa_off = random.randint(0, (date(2024, 12, 31) - date(2020, 1, 1)).days)
            fa = date(2020, 1, 1) + timedelta(days=fa_off)
            first_app_opens.append(fa.isoformat())
            la_off = random.randint(int(lo * 0.3), int(max(lo * 0.3 + 30, hi * 0.5)))
            la = TODAY - timedelta(days=la_off)
            la = max(la, fa + timedelta(days=7))
            last_app_opens.append(la.isoformat())
        else:
            first_app_opens.append("")
            last_app_opens.append("")

        # Email dates
        fe_off = random.randint(0, (date(2023, 12, 31) - date(2018, 1, 1)).days)
        fe = date(2018, 1, 1) + timedelta(days=fe_off)
        first_email_opens.append(fe.isoformat())
        le_off = random.randint(int(lo * 0.2), int(max(lo * 0.2 + 10, hi * 0.7)))
        le = TODAY - timedelta(days=le_off)
        le = max(le, fe + timedelta(days=7))
        last_email_opens.append(le.isoformat())

        alo, ahi = att_ranges[m]
        attendance_frequencies.append(random.randint(alo, ahi))

    match_prefs = rng.choice(["T20", "County Championship", "The Hundred", "All Formats"], n, p=[0.30, 0.30, 0.20, 0.20])
    fav_players = rng.choice(PLAYERS, n)
    preferred_stands = rng.choice(["OCS Stand", "Pavilion", "Bedser Stand", "Peter May Stand"], n)
    travel_methods = rng.choice(["Car", "Train", "Walk", "Bus"], n, p=[0.40, 0.35, 0.15, 0.10])
    season_ticket_years = np.clip(rng.normal(5, 6, n).astype(int), 0, 30)
    hospitality_interest = rng.choice(["Yes", "No"], n, p=[0.25, 0.75])
    corporate_package = rng.choice(["Yes", "No"], n, p=[0.15, 0.85])

    return pd.DataFrame({
        "Fan_ID": fan_ids,
        "Age": ages,
        "Gender": genders,
        "County": counties,
        "Membership_Category": membership_cats,
        "Fan_Type": fan_types,
        "HAS_APP": has_app,
        "Email_Campaigns_Received": email_campaigns,
        "Email_Opens": email_opens,
        "Email_Clicks": email_clicks,
        "InApp_Campaigns_Received": inapp_campaigns,
        "InApp_Opens": inapp_opens,
        "InApp_Clicks": inapp_clicks,
        "Article_Views": article_views,
        "Ticket_Purchases": ticket_purchases,
        "Membership_Purchases": membership_purchases,
        "Retail_Purchases": retail_purchases,
        "Total_Revenue": total_revenues,
        "First_Purchase_Date": first_purchase_dates,
        "Last_Purchase_Date": last_purchase_dates,
        "First_App_Open": first_app_opens,
        "Last_App_Open": last_app_opens,
        "First_Email_Open": first_email_opens,
        "Last_Email_Open": last_email_opens,
        "Join_Date": join_dates,
        "Match_Type_Preference": match_prefs,
        "Attendance_Frequency": attendance_frequencies,
        "Favourite_Player": fav_players,
        "Preferred_Stand": preferred_stands,
        "Travel_Method": travel_methods,
        "Season_Ticket_Years": season_ticket_years,
        "Hospitality_Interest": hospitality_interest,
        "Corporate_Package": corporate_package,
    })


if __name__ == "__main__":
    df = generate_sample_data(500)
    df.to_csv("cricintel_fan_sample.csv", index=False)
    print(f"Generated cricintel_fan_sample.csv — {len(df)} rows, {len(df.columns)} columns")
