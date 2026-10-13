import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

DB_FILE = "local_market_intelligence.db"


def run_market_analytics():
    """Generate descriptive statistics for Pennsylvania county data."""

    if not os.path.exists(DB_FILE):
        print(
            f"[ERROR] Database file '{DB_FILE}' not found. "
            "Run the ingestion script first!",
            file=sys.stderr,
        )
        return False

    engine = create_engine(f"sqlite:///{DB_FILE}")
    SessionLocal = sessionmaker(bind=engine)

    try:
        with SessionLocal() as db_session:
            print("=" * 54)
            print("PENNSYLVANIA MARKET INTELLIGENCE REPORT")
            print("=" * 54)

            summary = db_session.execute(
                text("""
                    SELECT
                        AVG(median_income)
                            AS average_county_median_income,
                        COUNT(*) AS county_count
                    FROM county_economic_metrics
                """)
            ).one()

            if summary.county_count == 0:
                print("[WARNING] No county records found.")
                return False

            county_average = float(
                summary.average_county_median_income
            )

            print(
                "\nAverage of county median household incomes: "
                f"${county_average:,.2f}"
            )
            print(f"County records analyzed: {summary.county_count}")

            top_five = db_session.execute(
                text("""
                    SELECT county_name, median_income
                    FROM county_economic_metrics
                    ORDER BY median_income DESC, county_name ASC
                    LIMIT 5
                """)
            ).all()

            print("\nTOP 5 COUNTIES BY MEDIAN HOUSEHOLD INCOME")

            for rank, row in enumerate(top_five, start=1):
                print(
                    f"{rank}. {row.county_name}: "
                    f"${row.median_income:,}"
                )

            local_counties = db_session.execute(
                text("""
                    SELECT
                        county_name,
                        median_income,
                        median_income - :reference_income
                            AS difference_from_average
                    FROM county_economic_metrics
                    WHERE county_name IN (
                        :lehigh,
                        :northampton
                    )
                    ORDER BY county_name
                """),
                {
                    "reference_income": county_average,
                    "lehigh": "Lehigh County",
                    "northampton": "Northampton County",
                },
            ).all()

            print(
                "\nLEHIGH VALLEY CONTEXT"
                " (relative to the county average)"
            )

            if not local_counties:
                print("[INFO] No matching local county records found.")

            for row in local_counties:
                difference = row.difference_from_average
                status = "ABOVE" if difference >= 0 else "BELOW"

                print(
                    f"{row.county_name}: ${row.median_income:,} "
                    f"({status} by ${abs(difference):,.2f})"
                )

            print("\n[ SUCCESS ] Analytics report completed.")
            return True

    except SQLAlchemyError as error:
        print(
            f"[ERROR] Database analytics failed: {error}",
            file=sys.stderr,
        )
        return False

    finally:
        engine.dispose()


if __name__ == "__main__":
    if not run_market_analytics():
        sys.exit(1)