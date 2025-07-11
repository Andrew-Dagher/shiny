# modules/sidebar_module.py
import os
import sqlite3
import pandas as pd

from shiny import ui, reactive, module

# ─── Load & transform DB once at import ─────────────────────────────────
_db_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "Dashboard.db")
)
_conn = sqlite3.connect(_db_path)
_df_all = pd.read_sql("SELECT * FROM group_performance", _conn, parse_dates=["start_date"])
_conn.close()

# Map DB to the fields your dashboard expects
_df_all = _df_all.assign(
    Month              = _df_all["start_date"],
    Group              = _df_all["parentgroupname"],
    Marketing_Tier     = _df_all["grp_marketing_tier"],
    Region             = _df_all["region"],
    Product            = _df_all["product"],
    Channel            = _df_all["incoming_channel"],
    Segment_Type       = _df_all["grp_segment"],
    Quotes             = _df_all["nb_quote"].astype(int),
    Sales              = (_df_all["nb_nwb"] + _df_all["nb_ren"]).astype(int),
    Written_Premiums   = _df_all["total_wp"].astype(float),
)
_df_all["Avg_Premium"] = _df_all.apply(
    lambda r: (r["total_wp"] / r["Sales"]) if r["Sales"] > 0 else 0, axis=1
)
_df_all["Avg_CLV"] = _df_all.apply(
    lambda r: (r["total_wp"] / r["inforce_clients"]) if r["inforce_clients"] > 0 else 0, axis=1
)
_df_all["Closing_Ratio"] = (_df_all["Sales"] / _df_all["Quotes"] * 100).round(2)

# Pre-compute for UI
_MIN_DATE, _MAX_DATE = _df_all["Month"].min(), _df_all["Month"].max()
_GROUPS   = sorted(_df_all["Group"].unique())
_TIERS    = sorted(_df_all["Marketing_Tier"].unique())
_REGIONS  = sorted(_df_all["Region"].unique())
_PRODUCTS = sorted(_df_all["Product"].unique())
_SEGMENTS = sorted(_df_all["Segment_Type"].unique())
_CHANNELS = sorted(_df_all["Channel"].unique())


@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),

        # 1) range slider for Month
        ui.input_slider(
            "month_range",
            "Time Period",
            min=_MIN_DATE,
            max=_MAX_DATE,
            value=(_MIN_DATE, _MAX_DATE),
            ticks=True,
            time_format="%b|%Y",
            drag_range=True,
            width="100%",
        ),

        # 2) multi-select group selector
        ui.input_selectize(
            "group",
            "Group",
            choices=_GROUPS,
            multiple=True,
        ),

        # the rest
        ui.input_select("marketing_tier", "Marketing Tier", choices=["All"] + _TIERS, selected="All"),
        ui.input_select("region",           "Region",          choices=["All"] + _REGIONS, selected="All"),
        ui.input_select("product",          "Product",         choices=["All"] + _PRODUCTS, selected="All"),
        ui.input_select("segment_type",     "Segment",         choices=["All"] + _SEGMENTS, selected="All"),
        ui.input_select("channel",          "Channel",         choices=["All"] + _CHANNELS, selected="All"),
    )


@module.server
def sidebar_server(input, output, session):
    @reactive.Calc
    def filtered_data():
        df = _df_all.copy()

        # date filter
        start, end = input.month_range()
        df = df[(df["Month"] >= start) & (df["Month"] <= end)]

        # group filter
        if input.group():
            df = df[df["Group"].isin(input.group())]

        # other dropdowns
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
