# modules/sidebar_module.py
from shiny import ui, reactive, module
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- sample data ---
np.random.seed(123)
num_months = 12
today = datetime.now()
dates = [(today - timedelta(days=30 * i)).strftime("%b %Y")
         for i in range(num_months - 1, -1, -1)]

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
    "Written_Premiums": np.random.randint(200_000, 500_000, num_months),
    "Avg_Premium": np.random.randint(800, 1500, num_months),
    "Avg_CLV": np.random.randint(3000, 8000, num_months),
})
data["Closing_Ratio"] = (data["Sales"] / data["Quotes"] * 100).round(2)


@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),
        ui.input_select(
            "time_period", "Time Period",
            choices=["Last 3 Months", "Last 6 Months", "Last 12 Months"],
            selected="Last 12 Months"
        ),
        ui.input_select(
            "group", "Group",
            choices=["All"] + groups,
            selected="All"
        ),
        ui.input_select(
            "marketing_tier", "Marketing Tier",
            choices=["All"] + tiers,
            selected="All"
        ),
        ui.input_select(
            "region", "Region",
            choices=["All"] + regions,
            selected="All"
        ),
        ui.input_select(
            "product", "Product",
            choices=["All"] + products,
            selected="All"
        ),
        ui.input_select(
            "segment_type", "Segment",
            choices=["All"] + segment_types,
            selected="All"
        ),
        ui.input_select(
            "channel", "Channel",
            choices=["All"] + channels,
            selected="All"
        ),
    )


@module.server
def sidebar_server(input, output, session):
    @reactive.calc
    def filtered_data():
        df = data.copy()
        # slice by time
        months_map = {"Last 3 Months": 3, "Last 6 Months": 6, "Last 12 Months": 12}
        df = df.tail(months_map[input.time_period()])
        # apply filters
        for fld, val in [
            ("Group", input.group()),
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
