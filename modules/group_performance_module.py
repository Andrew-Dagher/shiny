# modules/group_performance_module.py
from shiny import ui, module, render
import matplotlib.pyplot as plt

# reuse the same mapping for metrics
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
            ui.card_header("Group Performance Metrics"),
            ui.output_data_frame("group_monthly_data")
        ),
        ui.card(
            ui.card_header("Group Performance Comparison"),
            ui.input_select(
                "group_compare_metric",
                "Select Metric to Compare",
                choices=METRIC_LABELS,
                selected="Quotes"
            ),
            ui.output_plot("group_comparison_plot")
        )
    )

@module.server
def group_performance_server(input, output, session, filtered_data):
    @render.data_frame
    def group_monthly_data():
        df = filtered_data()
        # Hide filter-related columns
        cols = ["GroupID", "Group"] + list(METRIC_LABELS.keys())
        df2 = df[cols].copy()
        # Rename columns for readability
        rename_map = {
            "GroupID": "Group ID",
            **METRIC_LABELS
        }
        df2.rename(columns=rename_map, inplace=True)
        return df2

    @render.plot
    def group_comparison_plot():
        data = filtered_data()
        metric = input.group_compare_metric()
        grouped = (
            data.groupby('Group')[metric]
            .mean().reset_index()
            .sort_values(metric, ascending=False)
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(grouped['Group'], grouped[metric], color='tab:blue')
        ax.set_xlabel("Group")
        ax.set_ylabel(METRIC_LABELS[metric])
        ax.set_title(f"{METRIC_LABELS[metric]} by Group")
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
