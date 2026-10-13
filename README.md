# Pennsylvania Economic Intelligence Engine

An interactive economic analytics dashboard for exploring county-level median household income across Pennsylvania.

Built with Python, the U.S. Census Bureau API, SQLite, SQLAlchemy, Pandas, Matplotlib, and Shiny for Python.

## Features

- **Census data ingestion:** Retrieves county-level economic data through the Census API.
- **Data processing:** Transforms API responses into structured county records.
- **Database storage:** Stores county income estimates locally using SQLite and SQLAlchemy.
- **Economic analytics:** Ranks counties and calculates descriptive income statistics.
- **Interactive filtering:** Filters counties by a user-selected income threshold.
- **Data visualization:** Compares county income estimates against a reference benchmark.

## Technology Stack

- Python
- U.S. Census Bureau API
- SQLite and SQLAlchemy
- Pandas
- Matplotlib
- Shiny for Python
- `uv` for Python environment and dependency management

## Project Structure

```text
pennsylvania-economic-intelligence-engine/
├── analytics.py
├── app.py
├── market_intelligence_engine.py
├── README.md
└── .gitignore
```

## Getting Started

### Prerequisites

- Python
- [`uv`](https://docs.astral.sh/uv/)
- A valid U.S. Census Bureau API key

### 1. Clone the Repository

```bash
git clone https://github.com/FlareAntony/pennsylvania-economic-intelligence-engine.git
cd pennsylvania-economic-intelligence-engine
```

### 2. Create a Virtual Environment

```bash
uv venv
```

### 3. Install Dependencies

```bash
uv pip install requests python-dotenv sqlalchemy pandas matplotlib shiny
```

### 4. Configure Environment Variables

Create a local `.env` file in the project directory:

```dotenv
CENSUS_API_BASE_URL=https://api.census.gov/data/2022/acs/acs5
PA_STATE_FIPS=42
CENSUS_API_KEY=YOUR_CENSUS_API_KEY
```

The configured endpoint uses the U.S. Census Bureau's 2022 American Community Survey (ACS) 5-Year Estimates API.

`PA_STATE_FIPS=42` identifies Pennsylvania in Census geographic queries.

Replace `YOUR_CENSUS_API_KEY` with your own Census API key. Keep your local `.env` file private. Never commit API keys, credentials, or other secrets to GitHub.

### 5. Retrieve and Store Economic Data

```bash
uv run python market_intelligence_engine.py
```

This script requests county-level data, processes the API response, and stores valid records in the local SQLite database.

The database file, `local_market_intelligence.db`, is generated locally and should not be committed to the repository.

### 6. Run the Analytics Report

```bash
uv run python analytics.py
```

The report summarizes county income statistics, ranks counties, and compares selected Lehigh Valley counties with the county-level reference average.

### 7. Launch the Dashboard

```bash
uv run shiny run app.py --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

The `--reload` option supports development by reloading the application when code changes are detected. Restart the dashboard after refreshing the database so the application loads the updated records.

## Data and Methodology

The project uses Census variable `B19013_001E`, representing estimated median household income.

The dashboard calculates the arithmetic average of the county median household income estimates available in its local database. This is a county-level comparison benchmark, **not Pennsylvania's official statewide median household income**.

The Census data reference period depends on the API endpoint configured for the project. Consult the source dataset and survey period when interpreting results.

County median household income is not the same as individual earnings or total household wealth. Census estimates may also have sampling error and should be interpreted accordingly.

## Future Improvements

- Add automated tests for data processing and analytical calculations.
- Document the exact Census data source, endpoint, and reference period.
- Retrieve the official statewide estimate as a separate benchmark.
- Add historical economic trends and additional economic indicators.
- Improve database update reliability and data validation.
- Add a data refresh timestamp to the dashboard.
- Improve setup and deployment documentation.

## Development Note

This is a personal learning and portfolio project developed with AI-assisted code generation and debugging. The calculations, data handling, and results should be independently verified before the application is used for business or policy decisions.
