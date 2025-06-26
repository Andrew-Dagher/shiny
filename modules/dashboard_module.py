from shiny import ui, render, reactive, module
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

metrics = ['Quotes', 'Sales', 'Written_Premiums', 'Closing_Ratio', 'Avg_Premium', 'Avg_CLV']

@module.ui
def dashboard_ui():
    return ui.nav_panel(
        "Executive Overview",
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("KPI Data Table"),
                ui.output_data_frame("kpi_table")
            ),
            ui.card(
                ui.card_header("Performance Trends"),
                ui.div(
                    ui.input_checkbox_group(
                        "metrics",
                        "Select metrics to display:",
                        choices=metrics,
                        selected=["Quotes", "Sales", "Closing_Ratio"],
                        inline=True
                    ),
                    style="display: flex; align-items: center;"
                ),
                ui.output_plot("trend_plot"),
                ui.output_ui("trend_indicators")
            ),
            width=1/2
        )
    )

@module.server
def dashboard_server(input, output, session, filtered_data):

    @reactive.calc
    def get_kpi_summary():
        data = filtered_data()
        kpi_summary = {
            "Metric": ["Total Quotes", "Total Sales", "Total Written Premiums", "Avg Closing Ratio", "Avg Premium", "Avg CLV"],
            "Value": [
                f"{data['Quotes'].sum():,}",
                f"{data['Sales'].sum():,}",
                f"{data['Written_Premiums'].sum():,}",
                f"{data['Closing_Ratio'].mean():.2f}%",
                f"{data['Avg_Premium'].mean():.2f}",
                f"{data['Avg_CLV'].mean():.2f}",
            ],
            "Trend": []
        }

        data_sorted = data.sort_values("Month")
        for metric in metrics:
            if len(data_sorted) > 1:
                first_val = data_sorted[metric].iloc[0]
                last_val = data_sorted[metric].iloc[-1]
                if first_val != 0:
                    trend = ((last_val - first_val) / first_val) * 100
                else:
                    trend = 0
            else:
                trend = 0
            kpi_summary["Trend"].append(trend)

        return pd.DataFrame(kpi_summary)

    @render.data_frame
    def kpi_table():
        kpi_display = get_kpi_summary().copy()
        formatted_trends = []
        for trend_val in kpi_display["Trend"]:
            if trend_val == "N/A":
                formatted_trends.append("N/A")
            else:
                if trend_val > 0:
                    formatted_trends.append(f"+{trend_val:.2f}%")
                elif trend_val < 0:
                    formatted_trends.append(f"{trend_val:.2f}%")
                else:
                    formatted_trends.append(f"~ 0.00%")
        kpi_display["Trend"] = formatted_trends
        return render.DataGrid(kpi_display, width="100%", height=300)

    @render.plot
    def trend_plot():
        data = filtered_data().sort_values("Month")
        selected_metrics = input.metrics()
        fig, ax = plt.subplots(figsize=(10, 6))

        scale_factors = {
            "Quotes": 1,
            "Sales": 1,
            "Written_Premiums": 1/1000,
            "Closing_Ratio": 1,
            "Avg_Premium": 1,
            "Avg_CLV": 1/1000
        }

        column_map = {
            "Quotes": "Quotes",
            "Sales": "Sales",
            "Written_Premiums": "Written_Premiums",
            "Closing_Ratio": "Closing_Ratio",
            "Avg_Premium": "Avg_Premium",
            "Avg_CLV": "Avg_CLV"
        }

        for metric in selected_metrics:
            column = column_map[metric]
            factor = scale_factors[metric]
            ax.plot(data["Month"], data[column] * factor, marker="o", label=metric)

        ax.set_xlabel("Month")
        ax.set_ylabel("Value")
        ax.set_title("Performance Trends")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig

    @render.ui
    def trend_indicators():
        data = filtered_data().sort_values("Month")
        selected_metrics = input.metrics()
        column_map = {
            "Quotes": "Quotes",
            "Sales": "Sales",
            "Written_Premiums": "Written_Premiums",
            "Closing_Ratio": "Closing_Ratio",
            "Avg_Premium": "Avg_Premium",
            "Avg_CLV": "Avg_CLV"
        }

        indicators = []
        for metric in selected_metrics:
            column = column_map[metric]
            if len(data) >= 2:
                current = data[column].iloc[-1]
                previous = data[column].iloc[-2]
                if previous != 0:
                    pct_change = ((current - previous) / previous) * 100
                else:
                    pct_change = 0

                if pct_change > 0:
                    color = "green"
                    arrow = "↑"
                    sign = "+"
                elif pct_change < 0:
                    color = "red"
                    arrow = "↓"
                    sign = ""
                else:
                    color = "gray"
                    arrow = "→"
                    sign = ""

                indicators.append(
                    ui.div(
                        ui.h5(metric),
                        ui.p(
                            f"Month-over-month: {arrow} ",
                            ui.span(
                                f"{sign}{pct_change:.2f}%",
                                style=f"color: {color}; font-weight: bold;"
                            )
                        ),
                        style="margin-right: 15px; margin-bottom: 10px;"
                    )
                )
        return ui.div(
            ui.h4("Trend Analysis (Month-over-Month)"),
            ui.div(
                {"class": "d-flex flex-wrap"},
                *indicators
            ),
            style="margin-top: 15px;"
        )
