# modules/group_performance_module.py
from shiny import ui, module, render
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# mapping for display names
METRIC_LABELS = {
    "Quotes": "Quotes",
    "Sales": "Sales",
    "Written_Premiums": "Written Premiums",
    "Closing_Ratio": "Closing Ratio",
    "Avg_Premium": "Average Premium",
    "Avg_CLV": "Average CLV",
}

@module.ui
def group_performance_ui():
    return ui.nav_panel(
        "Group Performance",
        ui.card(
            ui.card_header("Top 30 Groups by Composite Score"),
            ui.output_data_frame("group_monthly_data"),
        ),
        ui.card(
            ui.card_header("Group Performance Comparison"),
            ui.input_select(
                "group_compare_metric",
                "Select Metric to Compare",
                choices=METRIC_LABELS,
                selected="Quotes",
            ),
            ui.output_plot("group_comparison_plot"),
        ),
    )

@module.server
def group_performance_server(input, output, session, filtered_data):
    @render.data_frame
    def group_monthly_data():
        df = filtered_data()

        # 1) aggregate each group's metrics
        agg = df.groupby("Group", as_index=False).agg({
            "Quotes": "sum",
            "Sales": "sum",
            "Written_Premiums": "sum",
            "Closing_Ratio": "mean",
            "Avg_Premium": "mean",
            "Avg_CLV": "mean",
        })

        # 2) normalize the three selection metrics
        for col in ["Quotes", "Sales", "Closing_Ratio"]:
            mn, mx = agg[col].min(), agg[col].max()
            agg[f"norm_{col}"] = np.where(mx > mn,
                                          (agg[col] - mn) / (mx - mn),
                                          0.0)

        # 3) composite score = average of normalized metrics
        agg["Composite"] = agg[["norm_Quotes", "norm_Sales", "norm_Closing_Ratio"]].mean(axis=1)

        # 4) pick top 30 by composite
        top30 = agg.nlargest(30, "Composite").copy()

        # 5) build the display table with all original metrics
        table = top30[["Group"] + list(METRIC_LABELS.keys())].rename(columns=METRIC_LABELS)

        return render.DataGrid(table, width="100%")

    @render.plot
    def group_comparison_plot():
        df = filtered_data()
        metric = input.group_compare_metric()

        # reuse composite ranking to get the same top30 
        agg = df.groupby("Group", as_index=False).agg({
            "Quotes": "sum",
            "Sales": "sum",
            "Closing_Ratio": "mean",
        })
        for col in ["Quotes", "Sales", "Closing_Ratio"]:
            mn, mx = agg[col].min(), agg[col].max()
            agg[f"norm_{col}"] = np.where(mx > mn,
                                          (agg[col] - mn) / (mx - mn),
                                          0.0)
        agg["Composite"] = agg[["norm_Quotes", "norm_Sales", "norm_Closing_Ratio"]].mean(axis=1)
        top_groups = agg.nlargest(30, "Composite")["Group"]

        # average selected metric for those top 30 groups
        grouped = (
            df[df["Group"].isin(top_groups)]
            .groupby("Group")[metric]
            .mean()
            .reset_index()
            .sort_values(metric, ascending=False)
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(grouped["Group"], grouped[metric], color="tab:blue")
        ax.set_xlabel("Group")
        ax.set_ylabel(METRIC_LABELS[metric])
        ax.set_title(f"{METRIC_LABELS[metric]} by Group (Top 30 Composite)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
