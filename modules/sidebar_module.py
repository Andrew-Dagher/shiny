# modules/sidebar_module.py
import os
import sqlite3
import pandas as pd

from shiny import ui, reactive, module

# ─── Load & preprocess the DB ────────────────────────────────────────────
_db_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "Dashboard.db")
)
_conn = sqlite3.connect(_db_path)
_raw = pd.read_sql("SELECT * FROM group_performance", _conn)
_conn.close()

# 1) parse fiscal code YYYYMM → Month (Timestamp)
_raw["Month"] = pd.to_datetime(
    _raw["sqapp_fiscal_period_cd"].astype(str),
    format="%Y%m",
    errors="coerce",
)

# 2) drop rows missing Month or parentgroupname
_raw.dropna(subset=["Month", "parentgroupname"], inplace=True)

# 3) fill numeric nulls so sums/means/ratios are safe
_for_zero = ["nb_quote", "nb_nwb", "nb_ren", "total_wp", "inforce_clients"]
for col in _for_zero:
    if col in _raw:
        _raw[col] = _raw[col].fillna(0)

# 4) map to the fields your dashboard expects
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

# 5) compute averages & closing ratio safely
_df_all["Avg_Premium"] = _df_all.apply(
    lambda r: (r["total_wp"] / r["Sales"]) if r["Sales"] > 0 else 0,
    axis=1,
)
_df_all["Avg_CLV"] = _df_all.apply(
    lambda r: (r["total_wp"] / r["inforce_clients"]) if r["inforce_clients"] > 0 else 0,
    axis=1,
)
_df_all["Closing_Ratio"] = (_df_all["Sales"] / _df_all["Quotes"] * 100).round(2)

# 6) compute slider bounds & dropdown choices from cleaned data
_MIN_DATE  = _df_all["Month"].min()
_MAX_DATE  = _df_all["Month"].max()
_GROUPS    = sorted(_df_all["Group"].dropna().unique())
_TIERS     = sorted(_df_all["Marketing_Tier"].dropna().unique())
_REGIONS   = sorted(_df_all["Region"].dropna().unique())
_PRODUCTS  = sorted(_df_all["Product"].dropna().unique())
_SEGMENTS  = sorted(_df_all["Segment_Type"].dropna().unique())
_CHANNELS  = sorted(_df_all["Channel"].dropna().unique())


@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),

        # slider now has real datetime bounds
        ui.input_slider(
            "month_range", "Time Period",
            min=_MIN_DATE, max=_MAX_DATE,
            value=(_MIN_DATE, _MAX_DATE),
            ticks=True,
            time_format="%b|%Y",
            drag_range=True,
            width="100%",
        ),

        ui.input_selectize(
            "group", "Group",
            choices=_GROUPS,
            multiple=True,
        ),

        ui.input_select(
            "marketing_tier", "Marketing Tier",
            choices=["All"] + _TIERS,
            selected="All",
        ),
        ui.input_select(
            "region", "Region",
            choices=["All"] + _REGIONS,
            selected="All",
        ),
        ui.input_select(
            "product", "Product",
            choices=["All"] + _PRODUCTS,
            selected="All",
        ),
        ui.input_select(
            "segment_type", "Segment",
            choices=["All"] + _SEGMENTS,
            selected="All",
        ),
        ui.input_select(
            "channel", "Channel",
            choices=["All"] + _CHANNELS,
            selected="All",
        ),
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
