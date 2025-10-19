[README.md](https://github.com/user-attachments/files/22988847/README.md)
# Movie Box Office Analytics (Pandas)

This project reproduces the analysis from a Jupyter/HTML assignment (movies box-office dataset) using a clean, reusable **Python script**. It reads four CSV files, merges them into a single dataset, and exposes multiple analyses via a simple CLI.

> Data fields and many queries mirror the original notebook you shared (e.g., columns like **`Worldwide Collection in Crores`**, **`Budget in Crores`**, **`IMDb Rating`**, **`Industry`**, **`Language`**, etc.).

## Files
- `movie_analytics.py` – main script with CLI (load, clean, merge, and run analyses; export results to CSV/Markdown)
- `README.md` – this guide

## Expected Input CSVs
Place these files in the same folder (or point to them with CLI flags):
- `Boxoffice_Fact.csv`
- `Director_dim.csv`
- `Genere_dim.csv`
- `Language_dim.csv`

> Column names should match the originals (e.g., `Title`, `Release Date`, `Verdict`, `IMDb Rating`, `Worldwide Collection in Crores`, etc.).

## Quickstart
```bash
# 1) (Optional) Create and activate a virtual environment
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies (pandas only)
pip install pandas

# 3) Run a full summary and export results under ./output
python movie_analytics.py --input-dir . --export --output-dir ./output

# 4) Run specific analyses (examples)
python movie_analytics.py totals
python movie_analytics.py top-films --metric worldwide --n 10
python movie_analytics.py counts-by year
python movie_analytics.py language-metrics
```

## CLI Overview
```bash
python movie_analytics.py [-h] [--input-dir INPUT_DIR] [--fact FACT] [--director DIRECTOR]
                          [--genre GENRE] [--language LANGUAGE] [--export]
                          [--output-dir OUTPUT_DIR]
                          {totals,top-films,counts-by,language-metrics,director-metrics,actor-metrics,runtime,industry-top,not-overseas,language-year,ott-metrics,report}
                          ...
```

### Commands
- `totals` – Total films, total budgets, worldwide, first day, overseas, and India gross
- `top-films` – Top N films by a metric (`worldwide`, `india`, `overseas`, `firstday`)
- `counts-by` – Counts by `year` or `weekday`
- `language-metrics` – Budget, worldwide collection by language
- `director-metrics` – Top directors by films and worldwide
- `actor-metrics` – Top actors by worldwide
- `runtime` – Longest and shortest films
- `industry-top` – Top N by industry (Bollywood/Tollywood/Kollywood/Mollywood/Sandalwood)
- `not-overseas` – Films with zero overseas collection
- `language-year` – Films count by language & year
- `ott-metrics` – OTT platform wise counts and language*OTT counts
- `report` – Generate a consolidated Markdown report with the most important tables

Each command supports `--export` and `--output-dir` to write CSV/Markdown.

## Data Cleaning
- Normalizes column names to snake_case (safe handling of spaces and punctuation)
- Converts numeric columns like `budget_in_crores`, `worldwide_collection_in_crores`,
  `india_gross_collection_in_crores`, `first_day_collection_worldwide_in_crores`
- Parses `release_date` to datetime; adds `year` and `week_days`

## License
MIT – feel free to use and adapt.
