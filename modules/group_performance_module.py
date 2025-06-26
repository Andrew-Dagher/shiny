from shiny import ui, module, render
import matplotlib.pyplot as plt

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
                choices=["Quotes","Sales","Closing_Ratio","Written_Premiums","Avg_Premium","Avg_CLV"],
                selected="Quotes"
            ),
            ui.output_plot("group_comparison_plot")
        )
    )

@module.server
def group_performance_server(input, output, session, filtered_data):
    @render.data_frame
    def group_monthly_data():
        return filtered_data()

    @render.plot
    def group_comparison_plot():
        data = filtered_data()
        metric = input.group_compare_metric()
        grouped = data.groupby('Group')[metric].mean().reset_index().sort_values(metric, ascending=False)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(grouped['Group'], grouped[metric])
        ax.set_title(f"{metric} by Group")
        return fig
