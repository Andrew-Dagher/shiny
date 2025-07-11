# modules/dashboard_module.py
from shiny import ui, render, reactive, module
import pandas as pd
import matplotlib.pyplot as plt

from modules.sidebar_module import data as full_data

_METRICS = [
    "Quotes",
    "Sales",
    "Written_Premiums",
    "Closing_Ratio",
    "Avg_Premium",
    "Avg_CLV",
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

@module.ui
def dashboard_ui():
    return ui.nav_panel(
        "Executive Overview",
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("KPI Data Table"),
                ui.div(
                    ui.input_switch(
                        "show_top30",
                        "Show Top 30 Affinity Groups",
                        value=False,
                    ),
                    style="margin-bottom:10px;",
                ),
                ui.output_ui("kpi_table"),
            ),
            ui.card(
                ui.card_header("Performance Trends"),
                ui.div(
                    ui.input_checkbox_group(
                        "metrics",
                        "Select metrics to display:",
                        choices=METRIC_LABELS,
                        selected=["Quotes", "Sales", "Closing_Ratio"],
                        inline=True,
                    ),
                    style="display:flex;align-items:center;",
                ),
                ui.output_plot("trend_plot"),
                ui.output_ui("trend_indicators"),
            ),
            width=1/2,
        ),
    )

@module.server
def dashboard_server(input, output, session, filtered_data):
    @reactive.calc
    def kpi_wide() -> pd.DataFrame:
        df = filtered_data()

        # pick categories
        if input.show_top30():
            aff = df[df.Segment_Type == "Affinity"]
            top30 = (
                aff
                .groupby("Group")["Quotes"]
                .sum()
                .nlargest(30)
                .index
            )
            cats = [("Top 30 Affinity", aff[aff.Group.isin(top30)])]
        else:
            cats = [
                ("Affinity", df[df.Segment_Type == "Affinity"]),
                ("Direct Market", df[df.Segment_Type == "Direct Market"]),
                ("Total", df),
            ]

        # format the last-month label as "Mon YYYY"
        if not df.empty:
            last_month_label = df["Month"].iloc[-1].strftime("%b %Y")
        else:
            last_month_label = ""

        rows = []
        # – Metric rows –
        for m in _METRICS:
            label = METRIC_LABELS[m]
            row = {"Metrics": f"<b>{label}</b>"}
            for cat_name, sub in cats:
                sub_s = sub.sort_values("Month")
                num = sub_s[m].mean() if m == "Closing_Ratio" else sub_s[m].sum()
                val = f"{num:.1f}%" if m == "Closing_Ratio" else f"{int(num)}"
                if len(sub_s) > 1:
                    first, last = sub_s[m].iloc[[0, -1]]
                    pct = 0 if first == 0 else (last - first) / first * 100
                else:
                    pct = 0
                row[f"{cat_name} {last_month_label}"] = val
                row[f"{cat_name} YoY"] = f"{pct:+.1f}%"
            rows.append(row)

        # – Phone row –
        row = {"Metrics": "&nbsp;&nbsp;&nbsp;Phone"}
        for cat_name, sub in cats:
            s = sub[sub.Channel == "In"].sort_values("Month")
            num = s[m].mean() if m == "Closing_Ratio" else s[m].sum()
            val = f"{num:.1f}%" if m == "Closing_Ratio" else f"{int(num)}"
            if len(s) > 1:
                first, last = s[m].iloc[[0, -1]]
                pct = 0 if first == 0 else (last - first) / first * 100
            else:
                pct = 0
            row[f"{cat_name} {last_month_label}"] = val
            row[f"{cat_name} YoY"] = f"{pct:+.1f}%"
        rows.append(row)

        # – Web row –
        row = {"Metrics": "&nbsp;&nbsp;&nbsp;Web"}
        for cat_name, sub in cats:
            s = sub[sub.Channel == "Web"].sort_values("Month")
            num = s[m].mean() if m == "Closing_Ratio" else s[m].sum()
            val = f"{num:.1f}%" if m == "Closing_Ratio" else f"{int(num)}"
            if len(s) > 1:
                first, last = s[m].iloc[[0, -1]]
                pct = 0 if first == 0 else (last - first) / first * 100
            else:
                pct = 0
            row[f"{cat_name} {last_month_label}"] = val
            row[f"{cat_name} YoY"] = f"{pct:+.1f}%"
        rows.append(row)

        wide = pd.DataFrame(rows)
        # enforce column order
        cols = ["Metrics"]
        for cat_name, _ in cats:
            cols += [f"{cat_name} {last_month_label}", f"{cat_name} YoY"]
        return wide[cols]

    @render.ui
    def kpi_table():
        df = kpi_wide()
        html = df.to_html(
            index=False,
            escape=False,
            classes="table table-sm",
        )
        styled = f"""
        <style>
          .kpi-table table {{
            border-collapse: collapse;
            width: 100%;
            font-size: calc(100% - 1px);
          }}
          .kpi-table th,
          .kpi-table td {{
            border: 1px solid #dee2e6;
            padding: 5px;
          }}
          .kpi-table th {{
            background-color: #28a745;
            color: white;
          }}
        </style>
        <div class="kpi-table">
          {html}
        </div>
        """
        return ui.HTML(styled)

    @render.plot
    def trend_plot():
        df = filtered_data().sort_values("Month")
        sel = input.metrics()
        scale = {
            "Quotes": 1,
            "Sales": 1,
            "Written_Premiums": 1/1000,
            "Closing_Ratio": 1,
            "Avg_Premium": 1,
            "Avg_CLV": 1/1000,
        }

        fig, ax = plt.subplots(figsize=(10, 6))
        x = range(len(df))
        bottom = [0] * len(df)

        # stacked bars
        for m in ("Quotes", "Sales"):
            if m in sel:
                vals = (df[m] * scale[m]).tolist()
                ax.bar(
                    x,
                    vals,
                    bottom=bottom,
                    width=0.6,
                    alpha=0.5,
                    color=COLORS[m],
                    label=METRIC_LABELS[m],
                )
                bottom = [b + v for b, v in zip(bottom, vals)]

        # line plots
        for m in sel:
            if m not in ("Quotes", "Sales", "Closing_Ratio"):
                ax.plot(
                    x,
                    df[m] * scale[m],
                    marker="o",
                    color=COLORS[m],
                    label=METRIC_LABELS[m],
                )

        # secondary axis for closing ratio
        h2, l2 = [], []
        if "Closing_Ratio" in sel:
            ax2 = ax.twinx()
            ax2.plot(
                x,
                df["Closing_Ratio"],
                marker="o",
                linestyle="--",
                color=COLORS["Closing_Ratio"],
                label="Closing Ratio",
            )
            ax2.set_ylabel("Closing Ratio (%)")
            h2, l2 = ax2.get_legend_handles_labels()

        # format axes
        ax.set_xticks(x)
        ax.set_xticklabels(df["Month"].dt.strftime("%b %Y"), rotation=45)
        ax.set_xlabel("Month")
        ax.set_ylabel("Value")
        ax.set_title("Performance Trends")
        ax.grid(True, linestyle="--", alpha=0.7)

        # combine legends
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles + h2, labels + l2, loc="upper left")

        fig.tight_layout()
        return fig

    @render.ui
    def trend_indicators():
        df = filtered_data().sort_values("Month")
        sel = input.metrics()
        items = []
        for m in sel:
            if len(df) < 2:
                continue
            cur, prev = df[m].iloc[-1], df[m].iloc[-2]
            pct = 0 if prev == 0 else (cur - prev) / prev * 100
            arrow = "▲" if pct > 0 else "▼" if pct < 0 else "→"
            color = "green" if pct > 0 else "red" if pct < 0 else "gray"
            items.append(
                ui.div(
                    ui.h5(METRIC_LABELS[m]),
                    ui.p(
                        f"{arrow} {pct:+.1f}%",
                        style=f"color:{color};font-weight:bold;",
                    ),
                    style="margin-right:15px;margin-bottom:10px;",
                )
            )
        return ui.div(
            ui.h4("Trend Analysis (Month-over-Month)"),
            ui.div({"class": "d-flex flex-wrap"}, items),
            style="margin-top:15px;",
        )
