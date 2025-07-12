# modules/sidebar_module.py

import os
import sqlite3
import pandas as pd
from shiny import ui, reactive, module

# ─── One‐time load & preprocess (runs once per worker process) ─────────
from database.load_data import initialize_database
initialize_database()

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "Dashboard.db")
)
_conn = sqlite3.connect(DB_PATH)
_raw = pd.read_sql("SELECT * FROM group_performance", _conn)
_conn.close()

# parse YYYYMM → Timestamp
codes = _raw["sqpmp_fiscal_period_cd"].fillna(0).astype(int).astype(str).str.zfill(6)
_raw["Month"] = pd.to_datetime(codes, format="%Y%m", errors="coerce")

# drop bad rows
_raw.dropna(subset=["Month", "parentgroupname"], inplace=True)

# zero‐fill numeric gaps
for col in ("nb_quote", "nb_nwb", "nb_ren", "total_wp", "inforce_clients"):
    if col in _raw:
        _raw[col] = _raw[col].fillna(0)

# remap to your UI’s schema
_df_all = _raw.assign(
    Group            = _raw["parentgroupname"],
    Marketing_Tier   = _raw["grp_marketing_tier"],
    Region           = _raw["region"],
    Product          = _raw["product"],
    Channel          = _raw["incoming_channel"],
    Segment_Type     = _raw["grp_segment"],
    Quotes           = _raw["nb_quote"].astype(int),
    Sales            = (_raw["nb_nwb"] + _raw["nb_ren"]).astype(int),
    Written_Premiums = _raw["total_wp"].astype(float),
)
_df_all["Avg_Premium"]   = _df_all.apply(lambda r: r.total_wp/r.Sales if r.Sales>0 else 0, axis=1)
_df_all["Avg_CLV"]       = _df_all.apply(lambda r: r.total_wp/r.inforce_clients if r.inforce_clients>0 else 0, axis=1)
_df_all["Closing_Ratio"] = (
    _df_all["Sales"] / _df_all["Quotes"] * 100
).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

# compute slider bounds & dropdown choices
_min_date = _df_all["Month"].min().to_pydatetime()
_max_date = _df_all["Month"].max().to_pydatetime()
_GROUPS    = sorted(_df_all["Group"].unique())
_TIERS     = sorted(_df_all["Marketing_Tier"].dropna().unique())
_REGIONS   = sorted(_df_all["Region"].dropna().unique())
_PRODUCTS  = sorted(_df_all["Product"].dropna().unique())
_SEGMENTS  = sorted(_df_all["Segment_Type"].dropna().unique())
_CHANNELS  = sorted(_df_all["Channel"].dropna().unique())


@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),

        ui.input_slider(
            "month_range", "Time Period",
            min=_min_date,
            max=_max_date,
            value=(_min_date, _max_date),
            ticks=True,
            time_format="%b|%Y",
            drag_range=True,
            width="100%",
        ),

        ui.input_selectize("group",        "Group",          choices=_GROUPS,   multiple=True),
        ui.input_select("marketing_tier",  "Marketing Tier", choices=["All"]+_TIERS,   selected="All"),
        ui.input_select("region",          "Region",         choices=["All"]+_REGIONS, selected="All"),
        ui.input_select("product",         "Product",        choices=["All"]+_PRODUCTS,selected="All"),
        ui.input_select("segment_type",    "Segment",        choices=["All"]+_SEGMENTS,selected="All"),
        ui.input_select("channel",         "Channel",        choices=["All"]+_CHANNELS,selected="All"),
    )


@module.server
def sidebar_server(input, output, session):
    @reactive.Calc
    def filtered_data():
        df = _df_all.copy()

        # date‐range filter
        start, end = input.month_range()
        df = df[(df["Month"] >= start) & (df["Month"] <= end)]

        # group multi‐select
        if input.group():
            df = df[df["Group"].isin(input.group())]

        # other dropdown filters
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
