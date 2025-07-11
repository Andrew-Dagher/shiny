# modules/sidebar_module.py

import os
import sqlite3
import pandas as pd
from shiny import ui, reactive, module

# ─── 1) Load & populate the DB if needed ────────────────────────────────
# (Only required if you need to rebuild your Dashboard.db on startup)
from database.load_data import initialize_database
initialize_database()

# ─── 2) Read the group_performance table ───────────────────────────────
db_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "Dashboard.db")
)
conn = sqlite3.connect(db_path)
raw = pd.read_sql("SELECT * FROM group_performance", conn)
conn.close()

# ─── 3) Turn fiscal code YYYYMM → proper Timestamp ──────────────────────
#    e.g. 202507 or 202507.0 → "202507" → Timestamp("2025-07-01")
codes = raw["sqpmp_fiscal_period_cd"].fillna(0).astype(int)
codes = codes.astype(str).str.zfill(6)
raw["Month"] = pd.to_datetime(codes, format="%Y%m", errors="coerce")

# ─── 4) Drop any rows missing Month or Group ────────────────────────────
raw = raw.dropna(subset=["Month", "parentgroupname"])

# ─── 5) Zero-fill numeric columns so sums/means never break ─────────────
for col in ("nb_quote", "nb_nwb", "nb_ren", "total_wp", "inforce_clients"):
    if col in raw.columns:
        raw[col] = raw[col].fillna(0)

# ─── 6) Map into the DataFrame your dashboard expects ───────────────────
df_all = raw.assign(
    Group            = raw["parentgroupname"],
    Marketing_Tier   = raw["grp_marketing_tier"],
    Region           = raw["region"],
    Product          = raw["product"],
    Channel          = raw["incoming_channel"],
    Segment_Type     = raw["grp_segment"],
    Quotes           = raw["nb_quote"].astype(int),
    Sales            = (raw["nb_nwb"] + raw["nb_ren"]).astype(int),
    Written_Premiums = raw["total_wp"].astype(float),
)
df_all["Avg_Premium"]   = df_all.apply(lambda r: r.total_wp/r.Sales if r.Sales>0 else 0, axis=1)
df_all["Avg_CLV"]       = df_all.apply(lambda r: r.total_wp/r.inforce_clients if r.inforce_clients>0 else 0, axis=1)
df_all["Closing_Ratio"] = (df_all["Sales"]/df_all["Quotes"]*100).round(2)

# ─── 7) Compute slider bounds (pure Python datetimes) ───────────────────
min_date = df_all["Month"].min().to_pydatetime()
max_date = df_all["Month"].max().to_pydatetime()

# ─── 8) Build your filter pick-lists ────────────────────────────────────
groups   = sorted(df_all["Group"].unique())
tiers    = sorted(df_all["Marketing_Tier"].dropna().unique())
regions  = sorted(df_all["Region"].dropna().unique())
products = sorted(df_all["Product"].dropna().unique())
segments = sorted(df_all["Segment_Type"].dropna().unique())
channels = sorted(df_all["Channel"].dropna().unique())


@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),

        ui.input_slider(
            "month_range", "Time Period",
            min=min_date,
            max=max_date,
            value=(min_date, max_date),
            ticks=True,
            time_format="%b|%Y",
            drag_range=True,
            width="100%",
        ),

        ui.input_selectize("group",        "Group",          choices=groups,   multiple=True),
        ui.input_select("marketing_tier",  "Marketing Tier", choices=["All"]+tiers,   selected="All"),
        ui.input_select("region",          "Region",         choices=["All"]+regions, selected="All"),
        ui.input_select("product",         "Product",        choices=["All"]+products,selected="All"),
        ui.input_select("segment_type",    "Segment",        choices=["All"]+segments,selected="All"),
        ui.input_select("channel",         "Channel",        choices=["All"]+channels,selected="All"),
    )


@module.server
def sidebar_server(input, output, session):
    @reactive.Calc
    def filtered_data():
        df = df_all.copy()

        # 1) date-range
        start, end = input.month_range()
        df = df[(df["Month"] >= start) & (df["Month"] <= end)]

        # 2) multi-group
        if input.group():
            df = df[df["Group"].isin(input.group())]

        # 3) other dropdowns
        for fld, val in [
            ("Marketing_Tier", input.marketing_tier()),
            ("Region",         input.region()),
            ("Product",        input.product()),
            ("Segment_Type",   input.segment_type()),
            ("Channel",        input.channel()),
        ]:
            if val and val != "All":
                df = df[df[fld] == val]

        return df

    return filtered_data
