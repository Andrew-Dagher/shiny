# modules/sidebar_module.py
from shiny import ui, reactive, module
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- sample data ---
np.random.seed(123)
num_months = 12
today = datetime.now()
dates = [
    (today - timedelta(days=30 * i)).strftime("%b %y")
    for i in range(num_months - 1, -1, -1)
]

groups = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
tiers = ["Premium", "Standard", "Basic"]
regions = ["North", "South", "East", "West", "Central"]
products = ["Home", "Auto"]
channels = ["In", "Web"]
segment_types = ["Affinity", "Direct Market"]

data = pd.DataFrame({
    "Month": dates,
    "Group": np.random.choice(groups, num_months),
    "Marketing_Tier": np.random.choice(tiers, num_months),
    "Region": np.random.choice(regions, num_months),
    "Product": np.random.choice(products, num_months),
    "Channel": np.random.choice(channels, num_months),
    "Segment_Type": np.random.choice(segment_types, num_months),
    "Quotes": np.random.randint(800, 1200, num_months),
    "Sales": np.random.randint(200, 500, num_months),
    "Written_Premiums": np.random.randint(200000, 500000, num_months),
    "Avg_Premium": np.random.randint(800, 1500, num_months),
    "Avg_CLV": np.random.randint(3000, 8000, num_months),
})
data["Closing_Ratio"] = (data["Sales"] / data["Quotes"] * 100).round(2)

# convert Month strings to actual dates for the slider
data["Month"] = pd.to_datetime(data["Month"], format="%b %y")

@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),
        # 1) range slider for Month, formatted as "Mon|YY"
        ui.input_slider(
            "month_range",
            "Time Period",
            min=data["Month"].min(),
            max=data["Month"].max(),
            value=(data["Month"].min(), data["Month"].max()),
            ticks=True,
            time_format="%b|%y",
            drag_range=True,
            width="100%",
        ),
        # 2) multi-select group selector (only existing groups allowed)
        ui.input_select(
            "group",
            "Group",
            choices=groups,
            multiple=True,
            # removed 'create' option so users cannot add arbitrary entries
        ),
        ui.input_select(
            "marketing_tier",
            "Marketing Tier",
            choices=["All"] + tiers,
            selected="All",
        ),
        ui.input_select(
            "region",
            "Region",
            choices=["All"] + regions,
            selected="All",
        ),
        ui.input_select(
            "product",
            "Product",
            choices=["All"] + products,
            selected="All",
        ),
        ui.input_select(
            "segment_type",
            "Segment",
            choices=["All"] + segment_types,
            selected="All",
        ),
        ui.input_select(
            "channel",
            "Channel",
            choices=["All"] + channels,
            selected="All",
        ),
    )

@module.server
def sidebar_server(input, output, session):
    @reactive.calc
    def filtered_data():
        df = data.copy()
        # apply the date-range filter
        start, end = input.month_range()
        df = df[(df["Month"] >= start) & (df["Month"] <= end)]
        # apply the multi-group filter (empty = all)
        selected_groups = input.group()
        if selected_groups:
            df = df[df["Group"].isin(selected_groups)]
        # other dropdown filters
        for fld, val in [
            ("Marketing_Tier", input.marketing_tier()),
            ("Region", input.region()),
            ("Product", input.product()),
            ("Segment_Type", input.segment_type()),
            ("Channel", input.channel()),
        ]:
            if val != "All":
                df = df[df[fld] == val]
        return df

    return filtered_data
