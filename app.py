import os

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from shiny import App, render, ui

DB_FILE = "local_market_intelligence.db"

COLUMNS = ["county_name", "median_income"]


def load_county_data():
    """Load and validate county income records from SQLite."""
    if not os.path.isfile(DB_FILE):
        print(
            f"[WARNING] Database '{DB_FILE}' not found. "
            "Run the ingestion script first."
        )
        return pd.DataFrame(columns=COLUMNS)

    engine = create_engine(f"sqlite:///{DB_FILE}")

    try:
        data = pd.read_sql_query(
            """
            SELECT county_name, median_income
            FROM county_economic_metrics
            """,
            con=engine,
        )
    except (SQLAlchemyError, pd.errors.DatabaseError) as error:
        print(f"[ERROR] Unable to load county data: {error}")
        return pd.DataFrame(columns=COLUMNS)
    finally:
        engine.dispose()

    if data.empty:
        return pd.DataFrame(columns=COLUMNS)

    data["median_income"] = pd.to_numeric(
        data["median_income"], errors="coerce"
    )

    data = data.dropna(
        subset=["county_name", "median_income"]
    )

    # Exclude invalid negative income estimates.
    data = data[data["median_income"] >= 0].copy()
    data["median_income"] = data["median_income"].astype(int)

    return data.sort_values(
        "median_income", ascending=False
    ).reset_index(drop=True)


df = load_county_data()

# This is the mean of county median incomes, not the
# actual statewide median household income.
county_average = (
    df["median_income"].mean() if not df.empty else None
)

if not df.empty:
    highest_county = df.iloc[0]
    highest_name = highest_county["county_name"]
    highest_income = f"${highest_county['median_income']:,}"

    average_display = f"${county_average:,.2f}"
    county_count_display = f"{len(df)} counties"

    # Round the slider maximum upward in $5,000 increments.
    observed_max = int(df["median_income"].max())
    slider_max = max(
        120000,
        ((observed_max + 4999) // 5000) * 5000,
    )
else:
    highest_name = "No data available"
    highest_income = "Run ingestion first"
    average_display = "Unavailable"
    county_count_display = "0 counties"
    slider_max = 200000

slider_value = min(50000, slider_max)

app_ui = ui.page_fluid(
    ui.tags.style("""
        body {
            background: #F3F6FC;
            color: #17243B;
            font-family: Inter, "Segoe UI", sans-serif;
        }

        .container-fluid {
            max-width: 1700px;
            padding: 24px 28px 36px;
        }

        .hero-header {
            background: linear-gradient(
                120deg, #101B33 0%, #193B65 65%, #087E8B 100%
            );
            padding: 32px 36px;
            border-radius: 22px;
            margin-bottom: 26px;
            box-shadow: 0 12px 28px rgba(16, 35, 65, 0.14);
        }

        .hero-kicker {
            color: #80E2E8;
            font-size: 12px;
            font-weight: 750;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .hero-header h1 {
            color: white;
            font-size: clamp(27px, 3vw, 39px);
            font-weight: 750;
            letter-spacing: -1px;
            margin: 0 0 10px;
        }

        .hero-subtitle {
            color: #D3DFEF;
            font-size: 15px;
            margin: 0;
            line-height: 1.6;
        }

        .kpi-row {
            margin-bottom: 26px;
        }

        .kpi-row .bslib-value-box {
            min-height: 160px;
            height: 100%;
            border: none !important;
            border-radius: 18px !important;
            overflow: hidden;
            box-shadow: 0 8px 20px rgba(21, 40, 70, 0.10);
            transition: transform 0.18s ease,
                        box-shadow 0.18s ease;
        }

        .kpi-row .bslib-value-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 14px 28px rgba(21, 40, 70, 0.16);
        }

        .kpi-row .bslib-value-box,
        .kpi-row .bslib-value-box * {
            color: #FFFFFF !important;
        }

        .kpi-blue .bslib-value-box {
            background: linear-gradient(135deg, #1D4ED8, #3478F6) !important;
        }

        .kpi-teal .bslib-value-box {
            background: linear-gradient(135deg, #087E8B, #0D9BA1) !important;
        }

        .kpi-cyan .bslib-value-box {
            background: linear-gradient(135deg, #087FAD, #16A6C5) !important;
        }

        .dashboard-grid .card {
            background: #FFFFFF;
            border: 1px solid #E0E7F0;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 5px 18px rgba(27, 47, 78, 0.06);
        }

        .dashboard-grid .card-header {
            background: #FFFFFF;
            color: #17243B;
            padding: 18px 22px;
            border-bottom: 1px solid #E8EDF5;
            font-weight: 700;
            font-size: 15px;
        }

        .dashboard-grid .card-body {
            padding: 22px;
        }

        .shiny-input-container label {
            color: #33445E;
            font-weight: 600;
            line-height: 1.6;
        }

        #data_grid table {
            width: 100%;
            border-collapse: collapse;
            font-variant-numeric: tabular-nums;
        }

        #data_grid th {
            color: #66758C;
            font-size: 11px;
            letter-spacing: 0.7px;
            text-transform: uppercase;
            border-bottom: 2px solid #E5EBF4;
            padding: 12px 10px;
        }

        #data_grid td {
            color: #26364F;
            padding: 12px 10px;
            border-bottom: 1px solid #EDF1F7;
        }

        #data_grid tbody tr:hover td {
            background: #F3F8FF;
        }

        #data_grid tbody tr:last-child td {
            border-bottom: none;
        }

        @media (max-width: 768px) {
            .container-fluid {
                padding: 15px;
            }

            .hero-header {
                padding: 25px 22px;
                border-radius: 16px;
            }

            .kpi-row .bslib-value-box {
                min-height: 130px;
            }
        }
    """),

    ui.tags.div(
        ui.tags.div(
            "PENNSYLVANIA  /  COUNTY ECONOMICS",
            class_="hero-kicker",
        ),
        ui.tags.h1(
            "Economic Intelligence Engine"
        ),
        ui.tags.p(
            "Explore county-level household income across Pennsylvania "
            "with interactive filters and comparative analytics.",
            class_="hero-subtitle",
        ),
        class_="hero-header",
    ),

    ui.tags.div(
        ui.layout_column_wrap(
            ui.tags.div(
                ui.value_box(
                    "Average of County Median Incomes",
                    average_display,
                    theme="primary",
                ),
                class_="kpi-blue",
            ),
            ui.tags.div(
                ui.value_box(
                    "Highest County Median Household Income",
                    highest_name,
                    highest_income,
                    theme="success",
                ),
                class_="kpi-teal",
            ),
            ui.tags.div(
                ui.value_box(
                    "Counties in Dataset",
                    county_count_display,
                    theme="info",
                ),
                class_="kpi-cyan",
            ),
            width=1 / 3,
        ),
        class_="kpi-row",
    ),

    ui.tags.div(
        ui.layout_columns(
            ui.card(
                ui.card_header("County Income Filters"),
                ui.input_slider(
                    "min_income",
                    "Show counties with median household income of at least:",
                    min=0,
                    max=slider_max,
                    value=slider_value,
                    step=5000,
                ),
                ui.output_table("data_grid"),
            ),
            ui.card(
                ui.card_header("County Income Comparisons"),
                ui.output_plot("income_chart"),
            ),
            col_widths=[5, 7],
        ),
        class_="dashboard-grid",
    ),
)

def server(input, output, session):

    def get_filtered_data():
        return df[
            df["median_income"] >= input.min_income()
        ]

    @output
    @render.plot
    def income_chart():
        filtered_df = get_filtered_data()
        fig, ax = plt.subplots(figsize=(10, 6))

        if filtered_df.empty:
            ax.text(
                0.5,
                0.5,
                "No counties meet this income threshold.",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_axis_off()
            fig.tight_layout()
            return fig

        plot_df = filtered_df.head(20)

        fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        positions = range(len(plot_df))

        ax.bar(
            positions,
            plot_df["median_income"],
            color="#3478F6",
            width=0.72,
            edgecolor="none",
            zorder=3,
        )

        if county_average is not None:
            ax.axhline(
                county_average,
                color="#0D9BA1",
                linestyle="--",
                linewidth=2,
                label=f"Average of county medians (${county_average:,.0f})",
                zorder=4,
            )
            ax.legend(
                frameon=True,
                facecolor="#FFFFFF",
                edgecolor="#E0E7F0",
                fontsize=9,
            )

        ax.set_xticks(list(positions))
        ax.set_xticklabels(
            plot_df["county_name"],
            rotation=42,
            ha="right",
        )

        ax.set_ylabel(
            "Median Household Income ($)",
            color="#33445E",
            labelpad=10,
        )
        ax.set_title(
            "Counties Meeting the Income Threshold",
            color="#17243B",
            fontweight="bold",
            pad=18,
        )

        ax.set_axisbelow(True)
        ax.grid(
            axis="y",
            color="#E5EBF4",
            linewidth=0.8,
        )

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D7E0EC")
        ax.spines["bottom"].set_color("#D7E0EC")

        ax.tick_params(colors="#52627A")
        ax.margins(x=0.04)

        fig.tight_layout()
        return fig

    @output
    @render.table
    def data_grid():
        filtered_df = get_filtered_data().copy()

        filtered_df["median_income"] = filtered_df[
            "median_income"
        ].map(lambda income: f"${income:,}")

        return filtered_df.rename(
            columns={
                "county_name": "County",
                "median_income": "Median Household Income",
            }
        )


app = App(app_ui, server)