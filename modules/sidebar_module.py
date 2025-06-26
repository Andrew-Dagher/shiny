from shiny import ui, reactive, module
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate the sample data
np.random.seed(123)
num_months = 12
current_date = datetime.now()
dates = [(current_date - timedelta(days=30*i)).strftime('%b %Y') for i in range(num_months-1, -1, -1)]

groups = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
marketing_tiers = ['Premium', 'Standard', 'Basic']
regions = ['North', 'South', 'East', 'West', 'Central']
segments = ['Individual', 'Small Business', 'Corporate', 'Enterprise']

group_ids = [f"G-{np.random.randint(1000, 9999)}" for _ in range(num_months)]

# Generate raw data
data = pd.DataFrame({
    'Month': dates,
    'GroupID': group_ids,
    'Group': np.random.choice(groups, num_months),
    'Marketing_Tier': np.random.choice(marketing_tiers, num_months),
    'Region': np.random.choice(regions, num_months),
    'Segment': np.random.choice(segments, num_months),
    'Quotes': np.random.randint(800, 1200, num_months),
    'Sales': np.random.randint(200, 500, num_months),
    'Written_Premiums': np.random.randint(200000, 500000, num_months),
    'Avg_Premium': np.random.randint(800, 1500, num_months),
    'Avg_CLV': np.random.randint(3000, 8000, num_months),
})
data['Closing_Ratio'] = (data['Sales'] / data['Quotes'] * 100).round(2)

@module.ui
def sidebar_ui():
    return ui.sidebar(
        ui.h3("Filters"),
        ui.input_select(
            "time_period",
            "Time Period",
            choices=["Last 3 Months","Last 6 Months","Last 12 Months"],
            selected="Last 12 Months",
        ),
        ui.input_select(
            "group",
            "Group",
            choices=["All"] + groups,
            selected="All",
        ),
        ui.input_select(
            "marketing_tier",
            "Marketing Tier",
            choices=["All"] + marketing_tiers,
            selected="All",
        ),
        ui.input_select(
            "region",
            "Region",
            choices=["All"] + regions,
            selected="All",
        ),
        ui.input_select(
            "segment",
            "Segment",
            choices=["All"] + segments,
            selected="All",
        ),
    )

@module.server
def sidebar_server(input, output, session):
    @reactive.calc
    def filtered_data():
        months = 12
        if input.time_period() == "Last 3 Months":
            months = 3
        elif input.time_period() == "Last 6 Months":
            months = 6

        filtered = data.tail(months).copy()

        if input.group() != "All":
            filtered = filtered[filtered['Group'] == input.group()]
        if input.marketing_tier() != "All":
            filtered = filtered[filtered['Marketing_Tier'] == input.marketing_tier()]
        if input.region() != "All":
            filtered = filtered[filtered['Region'] == input.region()]
        if input.segment() != "All":
            filtered = filtered[filtered['Segment'] == input.segment()]

        return filtered

    return filtered_data
