from shiny import ui, render, reactive, module
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

_METRICS = [
    "Quotes",
    "Sales",
    "Written_Premiums",
    "Closing_Ratio",
    "Avg_Premium",
    "Avg_CLV",
]


@module.ui
def dashboard_ui():
    """
    Executive-overview tab.
    """
    return ui.nav_panel(
        "Executive Overview",
        ui.layout_column_wrap(
            # ---- KPI table --------------------------------------------------
            ui.card(
                ui.card_header("KPI Data Table"),
                ui.output_data_frame("kpi_table"),
            ),
            # ---- Trend chart -------------------------------------------------
            ui.card(
                ui.card_header("Performance Trends"),
                ui.div(
                    ui.input_checkbox_group(
                        "metrics",
                        "Select metrics to display:",
                        choices=_METRICS,
                        selected=["Quotes", "Sales", "Closing_Ratio"],
                        inline=True,
                    ),
                    style="display:flex;align-items:center;",
                ),
                ui.output_plot("trend_plot"),
                ui.output_ui("trend_indicators"),
            ),
            width=1 / 2,
        ),
    )


@module.server
def dashboard_server(input, output, session, filtered_data):
    # ---- helpers -------------------------------------------------------
    @reactive.calc
    def kpi_summary() -> pd.DataFrame:
        df = filtered_data()

        summary = {
            "Metric": [
                "Total Quotes",
                "Total Sales",
                "Total Written Premiums",
                "Avg Closing Ratio",
                "Avg Premium",
                "Avg CLV",
            ],
            "Value": [
                f"{df['Quotes'].sum():,}",
                f"{df['Sales'].sum():,}",
                f"{df['Written_Premiums'].sum():,}",
                f"{df['Closing_Ratio'].mean():.2f} %",
                f"{df['Avg_Premium'].mean():.2f}",
                f"{df['Avg_CLV'].mean():.2f}",
            ],
            "Trend": [],
        }

        # compute pct change over the whole period
        df_sorted = df.sort_values("Month")
        for metric in _METRICS:
            if len(df_sorted) > 1:
                first, last = df_sorted[metric].iloc[[0, -1]]
                trend = 0 if first == 0 else (last - first) / first * 100
            else:
                trend = 0
            summary["Trend"].append(trend)

        return pd.DataFrame(summary)

    # ---- outputs -------------------------------------------------------
    @render.data_frame
    def kpi_table():
        tbl = kpi_summary().copy()

        # pretty-print the trend column
        fmt = []
        for v in tbl["Trend"]:
            if v > 0:
                fmt.append(f"+{v:.2f} %")
            elif v < 0:
                fmt.append(f"{v:.2f} %")
            else:
                fmt.append("~ 0.00 %")
        tbl["Trend"] = fmt

        # returning a bare DataFrame is now the recommended way
        return tbl

    @render.plot
    def trend_plot():
        df = filtered_data().sort_values("Month")
        selected = input.metrics()

        fig, ax = plt.subplots(figsize=(10, 6))

        scale = {
            "Quotes": 1,
            "Sales": 1,
            "Written_Premiums": 1 / 1000,
            "Closing_Ratio": 1,
            "Avg_Premium": 1,
            "Avg_CLV": 1 / 1000,
        }

        for metric in selected:
            ax.plot(
                df["Month"],
                df[metric] * scale[metric],
                marker="o",
                label=metric.replace("_", " "),
            )

        ax.set_xlabel("Month")
        ax.set_ylabel("Value")
        ax.set_title("Performance Trends")
        ax.grid(True, linestyle="--", alpha=0.7)
        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()
        return fig

    @render.ui
    def trend_indicators():
        df = filtered_data().sort_values("Month")
        selected = input.metrics()

        indicators = []
        for metric in selected:
            if len(df) < 2:
                continue

            curr, prev = df[metric].iloc[-1], df[metric].iloc[-2]
            pct = 0 if prev == 0 else (curr - prev) / prev * 100
            arrow = "↑" if pct > 0 else "↓" if pct < 0 else "→"
            color = "green" if pct > 0 else "red" if pct < 0 else "gray"
            sign = "+" if pct > 0 else ""

            indicators.append(
                ui.div(
                    ui.h5(metric.replace("_", " ")),
                    ui.p(
                        f"Month-over-month: {arrow} ",
                        ui.span(
                            f"{sign}{pct:.2f} %",
                            style=f"color:{color};font-weight:bold;",
                        ),
                    ),
                    style="margin-right:15px;margin-bottom:10px;",
                )
            )

        return ui.div(
            ui.h4("Trend Analysis (Month-over-Month)"),
            ui.div({"class": "d-flex flex-wrap"}, *indicators),
            style="margin-top:15px;",
        )
