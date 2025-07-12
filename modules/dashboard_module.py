# modules/dashboard_module.py

from shiny import ui, render, reactive, module
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ─── Constants ─────────────────────────────────────────────────────────────
_METRICS = [
    "Quotes", "Sales", "Written_Premiums",
    "Closing_Ratio", "Avg_Premium", "Avg_CLV",
]

METRIC_LABELS = {
    "Quotes": "Quotes",
    "Sales": "Sales",
    "Written_Premiums": "Written Premiums",
    "Closing_Ratio": "Closing Ratio",
    "Avg_Premium": "Average Premium",
    "Avg_CLV": "Average CLV",
}

COLORS = {
    "Quotes": "tab:blue",
    "Sales": "tab:orange",
    "Written_Premiums": "tab:green",
    "Avg_Premium": "tab:purple",
    "Avg_CLV": "tab:brown",
    "Closing_Ratio": "tab:green",
}

SCALE = {
    "Quotes": 1,
    "Sales": 1,
    "Written_Premiums": 1/1000,
    "Closing_Ratio": 1,
    "Avg_Premium": 1,
    "Avg_CLV": 1/1000,
}


# ─── UI ─────────────────────────────────────────────────────────────────────
@module.ui
def dashboard_ui():
    return ui.nav_panel(
        "Executive Overview",

        # KPI table
        ui.card(
            ui.card_header("KPI Data Table"),
            ui.div(
                ui.input_switch("show_top30", "Show Top 30 Affinity Groups", value=False),
                style="margin-bottom:10px;",
            ),
            ui.output_ui("kpi_table"),
        ),

        # Bottom row: Sales/Closing on left, Others on right
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("Sales & Closing Trends"),
                ui.output_plot("sales_closing_plot"),
            ),
            ui.card(
                ui.card_header("Other Metrics Trends"),
                ui.input_checkbox_group(
                    "other_metrics",
                    "Select other metrics:",
                    choices={
                        k: v
                        for k, v in METRIC_LABELS.items()
                        if k not in ("Quotes", "Sales", "Closing_Ratio")
                    },
                    selected=["Written_Premiums", "Avg_Premium", "Avg_CLV"],
                    inline=True,
                ),
                ui.output_plot("other_trends_plot"),
                ui.output_ui("other_trend_indicators"),
            ),
            width=1/2,
        ),
    )


# ─── Server ─────────────────────────────────────────────────────────────────
@module.server
def dashboard_server(input, output, session, filtered_data):

    @reactive.Calc
    def kpi_wide() -> pd.DataFrame:
        df = filtered_data().copy()
        df.dropna(subset=["Month", "Group"], inplace=True)

        # zero‐fill and eliminate any remaining infinities in every metric
        df[_METRICS] = df[_METRICS].replace([np.inf, -np.inf], 0).fillna(0).astype(float)

        # pick cats
        if input.show_top30():
            aff   = df[df.Segment_Type == "Affinity"]
            top30 = aff.groupby("Group")["Quotes"].sum().nlargest(30).index
            cats  = [("Top 30 Affinity", aff[aff.Group.isin(top30)])]
        else:
            cats = [
                ("Affinity",      df[df.Segment_Type == "Affinity"]),
                ("Direct Market", df[df.Segment_Type == "Direct Market"]),
                ("Total",         df),
            ]

        last_lbl = df["Month"].iloc[-1].strftime("%b %Y") if not df.empty else ""
        rows = []

        for m in _METRICS:
            label = METRIC_LABELS[m]

            for prefix, chan in [(f"<b>{label}</b>", None), ("   Phone", "In"), ("   Web", "Web")]:
                row = {"Metrics": prefix}
                for cat_name, sub in cats:
                    sub = sub if chan is None else sub[sub.Channel == chan]

                    # build the series, replace inf, fill NaN, cast float
                    s = (
                        sub.sort_values("Month")[m]
                        .replace([np.inf, -np.inf], 0)
                        .fillna(0)
                        .astype(float)
                    )

                    # safe percent‐change
                    if len(s) >= 2 and s.iloc[0] not in (0, np.nan):
                        pct = (s.iloc[-1] - s.iloc[0]) / s.iloc[0] * 100
                    else:
                        pct = 0

                    total = s.mean() if m == "Closing_Ratio" else s.sum()
                    val   = f"{total:.1f}%" if m == "Closing_Ratio" else f"{int(total)}"

                    row[f"{cat_name} {last_lbl}"] = val
                    row[f"{cat_name} YoY"]       = f"{pct:+.1f}%"
                rows.append(row)

        wide = pd.DataFrame(rows).fillna("")
        cols = ["Metrics"] + [
            c for cat, _ in cats for c in (f"{cat} {last_lbl}", f"{cat} YoY")
        ]
        return wide[cols]

    @render.ui
    def kpi_table():
        df   = kpi_wide()
        html = df.to_html(index=False, escape=False, classes="table table-sm")
        styled = f"""
<style>
.kpi-table table {{ border-collapse: collapse; width:100%; font-size:calc(100% - 1px); }}
.kpi-table th, .kpi-table td {{ border:1px solid #dee2e6; padding:5px; }}
.kpi-table th {{ background-color:#28a745; color:white; }}
</style>
<div class="kpi-table">
{html}
</div>
"""
        return ui.HTML(styled)

    @render.plot
    def sales_closing_plot():
        df = filtered_data().sort_values("Month").copy()
        df[_METRICS] = df[_METRICS].replace([np.inf, -np.inf], 0).fillna(0).astype(float)

        x      = range(len(df))
        bottom = [0] * len(df)
        fig, ax = plt.subplots(figsize=(10, 6))

        for m in ("Quotes", "Sales"):
            vals = (df[m] * SCALE[m]).tolist()
            ax.bar(x, vals, bottom=bottom, width=0.6,
                   alpha=0.5, color=COLORS[m], label=METRIC_LABELS[m])
            bottom = [b + v for b, v in zip(bottom, vals)]

        ax2 = ax.twinx()
        ax2.plot(x, df["Closing_Ratio"], marker="o", linestyle="--",
                 color=COLORS["Closing_Ratio"], label=METRIC_LABELS["Closing_Ratio"])
        ax2.set_ylabel("Closing Ratio (%)")

        ax.set_xticks(x)
        ax.set_xticklabels(df["Month"].dt.strftime("%b %Y"), rotation=45)
        ax.set_xlabel("Month")
        ax.set_ylabel("Value")
        ax.set_title("Sales & Closing Trends")

        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="upper left")

        fig.tight_layout()
        return fig

    @render.plot
    def other_trends_plot():
        df = filtered_data().sort_values("Month").copy()
        df[_METRICS] = df[_METRICS].replace([np.inf, -np.inf], 0).fillna(0).astype(float)
        sel = input.other_metrics()
        x   = range(len(df))

        fig, ax = plt.subplots(figsize=(10, 6))
        for m in sel:
            ax.plot(x, df[m] * SCALE[m], marker="o",
                    color=COLORS[m], label=METRIC_LABELS[m])

        ax.set_xticks(x)
        ax.set_xticklabels(df["Month"].dt.strftime("%b %Y"), rotation=45)
        ax.set_xlabel("Month")
        ax.set_ylabel("Value")
        ax.set_title("Other Metrics Trends")
        ax.legend(loc="upper left")
        fig.tight_layout()
        return fig

    @render.ui
    def other_trend_indicators():
        df = filtered_data().sort_values("Month").copy()
        df[_METRICS] = df[_METRICS].replace([np.inf, -np.inf], 0).fillna(0).astype(float)
        items = []
        for m in input.other_metrics():
            s = df[m]
            if len(s) >= 2 and s.iloc[-2] not in (0, np.nan):
                pct = (s.iloc[-1] - s.iloc[-2]) / s.iloc[-2] * 100
            else:
                pct = 0
            arrow = "▲" if pct > 0 else "▼" if pct < 0 else "→"
            color = "green" if pct > 0 else "red" if pct < 0 else "gray"
            items.append(
                ui.div(
                    ui.h5(METRIC_LABELS[m]),
                    ui.p(f"{arrow} {pct:+.1f}%", style=f"color:{color};font-weight:bold;"),
                    style="margin-right:15px;margin-bottom:10px;"
                )
            )
        return ui.div(
            ui.h4("Trend Analysis (Month-over-Month)"),
            ui.div({"class": "d-flex flex-wrap"}, items),
            style="margin-top:15px;"
        )
