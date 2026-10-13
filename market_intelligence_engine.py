import os
import sys
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BASE_URL = os.getenv("CENSUS_API_BASE_URL")
STATE_FIPS = os.getenv("PA_STATE_FIPS")
API_KEY = os.getenv("CENSUS_API_KEY")

if not BASE_URL or not STATE_FIPS or not API_KEY:
    print("[ERROR] Missing required configuration items in .env file.", file=sys.stderr)
    sys.exit(1)

DB_FILE = "local_market_intelligence.db"
Engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

class CountyEconomicMetric(Base):
    __tablename__ = "county_economic_metrics"
    id = Column(Integer, primary_key=True, index=True)
    county_name = Column(String, unique=True, nullable=False)
    median_income = Column(Integer, nullable=False)
    county_code = Column(String, unique=True, nullable=False)

def fetch_local_economic_data():
    clean_key = API_KEY.strip()
    params = {
        "get": "NAME,B19013_001E",
        "for": "county:*",
        "in": f"state:{STATE_FIPS}",
        "key": clean_key
    }
    
    print(f"[INFO] Initiating request to Census API...")
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Network error occurred: {err}", file=sys.stderr)
        return None

    try:
        return response.json()
    except ValueError:
        return None

def process_raw_data(raw_data):
    if not isinstance(raw_data, list) or len(raw_data) < 2:
        raise ValueError("Census API response is empty or malformed.")

    headers = raw_data[0]

    if not isinstance(headers, list):
        raise ValueError("Census API response has invalid headers.")

    required_headers = {"NAME", "B19013_001E", "county"}
    missing_headers = required_headers.difference(headers)

    if missing_headers:
        raise ValueError(
            f"Census API response is missing columns: "
            f"{sorted(missing_headers)}"
        )

    cleaned_records = []
    state_suffix = ", Pennsylvania"

    for row in raw_data[1:]:
        if not isinstance(row, list) or len(row) != len(headers):
            continue

        record = dict(zip(headers, row))

        try:
            income = int(record["B19013_001E"])
        except (ValueError, TypeError):
            continue

        if income < 0:
            continue

        county_code = record.get("county")
        county_name = record.get("NAME")

        if not county_code or not county_name:
            continue

        county_name = str(county_name).strip()

        if county_name.endswith(state_suffix):
            county_name = county_name[:-len(state_suffix)]

        cleaned_records.append({
            "county_name": county_name,
            "median_income": income,
            "county_code": str(county_code).zfill(3),
        })

    return cleaned_records

def save_data_to_sql(structured_data):
    if not structured_data:
        print("[WARNING] No valid county records to save.")
        return

    Base.metadata.create_all(bind=Engine)

    db_session = SessionLocal()

    try:
        existing_rows = (
            db_session.query(CountyEconomicMetric).all()
        )

        existing_by_code = {
            row.county_code: row
            for row in existing_rows
        }

        for record in structured_data:
            county_code = record["county_code"]
            existing_row = existing_by_code.get(county_code)

            if existing_row:
                existing_row.median_income = record["median_income"]
                existing_row.county_name = record["county_name"]
            else:
                new_row = CountyEconomicMetric(
                    county_name=record["county_name"],
                    median_income=record["median_income"],
                    county_code=county_code,
                )

                db_session.add(new_row)
                existing_by_code[county_code] = new_row

        db_session.commit()

        print(
            f"[SUCCESS] Saved {len(structured_data)} county records."
        )

    except Exception:
        db_session.rollback()
        print(
            "[ERROR] Database update failed. "
            "All changes in this batch were rolled back.",
            file=sys.stderr,
        )
        raise

    finally:
        db_session.close()

if __name__ == "__main__":
    raw_payload = fetch_local_economic_data()
    
    if raw_payload:
        structured_data = process_raw_data(raw_payload)
        print(f"[SUCCESS] Ingested {len(structured_data)} raw memory array records.")
        save_data_to_sql(structured_data)