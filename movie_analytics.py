#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Movie Box Office Analytics (Pandas CLI)

Recreates and extends a set of analyses over a movies box-office dataset.
- Reads: Boxoffice_Fact.csv, Director_dim.csv, Genere_dim.csv, Language_dim.csv
- Cleans and merges into a single DataFrame
- Provides multiple CLI subcommands to run analyses and export results

Author: <Your Name>
License: MIT
"""

import argparse
import os
from typing import Tuple, Dict
import pandas as pd

# -------------------------
# Utilities
# -------------------------
DEF_FACT = "Boxoffice_Fact.csv"
DEF_DIR = "Director_dim.csv"
DEF_GEN = "Genere_dim.csv"
DEF_LANG = "Language_dim.csv"

NUM_COLS = [
    "budget_in_crores",
    "first_day_collection_worldwide_in_crores",
    "worldwide_collection_in_crores",
    "overseas_collection_in_crores",
    "india_gross_collection_in_crores",
    "imdb_rating",
    "runtime_mins",
]


def snake(s: str) -> str:
    return (
        s.strip()
        .lower()
        .replace("/", "_")
        .replace(" ", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace("-", "_")
        .replace("+", "plus")
        .replace("__", "_")
    )


def load_data(
    input_dir: str,
    fact: str = DEF_FACT,
    director: str = DEF_DIR,
    genre: str = DEF_GEN,
    language: str = DEF_LANG,
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    paths = {
        "fact": os.path.join(input_dir, fact),
        "director": os.path.join(input_dir, director),
        "genre": os.path.join(input_dir, genre),
        "language": os.path.join(input_dir, language),
    }
    df1 = pd.read_csv(paths["fact"])  # main facts
    df2 = pd.read_csv(paths["director"])  # director_dim
    df3 = pd.read_csv(paths["genre"])  # genre_dim
    df4 = pd.read_csv(paths["language"])  # language_dim

    # Normalize column names
    df1.columns = [snake(c) for c in df1.columns]
    df2.columns = [snake(c) for c in df2.columns]
    df3.columns = [snake(c) for c in df3.columns]
    df4.columns = [snake(c) for c in df4.columns]

    # Merge similar to original notebook
    df12 = pd.merge(df1, df2, left_on="directorid", right_on="director_id", how="left")
    df123 = pd.merge(df12, df3, on="genreid", how="left")
    data = pd.merge(df123, df4, on="languageid", how="left")

    # Type conversions
    for c in NUM_COLS:
        if c in data.columns:
            data[c] = pd.to_numeric(data[c], errors="coerce")
    if "release_date" in data.columns:
        data["release_date"] = pd.to_datetime(data["release_date"], errors="coerce")
        data["year"] = data["release_date"].dt.year
        data["week_days"] = data["release_date"].dt.day_name()

    # Clean verdict and ott platform if present
    if "verdict" in data.columns:
        data["verdict"] = data["verdict"].astype(str).str.replace(":", "", regex=False).str.strip()
    if "ott_platform" in data.columns:
        data["ott_platform"] = data["ott_platform"].astype(str).str.capitalize().str.strip()

    return data, paths


# -------------------------
# Analyses
# -------------------------

def totals(data: pd.DataFrame) -> pd.DataFrame:
    out = {
        "total_films": int(data["title"].count()),
        "total_budget_crores": float(data["budget_in_crores"].sum()),
        "total_worldwide_crores": float(data["worldwide_collection_in_crores"].sum()),
        "total_firstday_crores": float(data["first_day_collection_worldwide_in_crores"].sum()),
        "total_overseas_crores": float(data["overseas_collection_in_crores"].sum()),
        "total_india_crores": float(data["india_gross_collection_in_crores"].sum()),
    }
    return pd.DataFrame([out])


def top_films(data: pd.DataFrame, metric: str = "worldwide", n: int = 10) -> pd.DataFrame:
    mapping = {
        "worldwide": "worldwide_collection_in_crores",
        "india": "india_gross_collection_in_crores",
        "overseas": "overseas_collection_in_crores",
        "firstday": "first_day_collection_worldwide_in_crores",
    }
    col = mapping.get(metric.lower())
    if not col or col not in data.columns:
        raise ValueError(f"Unsupported metric: {metric}")
    return data[["title", col]].sort_values(col, ascending=False).head(n).reset_index(drop=True)


def counts_by(data: pd.DataFrame, by: str = "year") -> pd.DataFrame:
    if by == "year":
        return data.groupby(["year"])[["title"]].count().rename(columns={"title": "count"}).reset_index()
    if by == "weekday":
        return data.groupby(["week_days"])[["title"]].count().rename(columns={"title": "count"}).reset_index()
    raise ValueError("by must be 'year' or 'weekday'")


def language_metrics(data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {
        "budget_by_language": data.groupby(["language"])[["budget_in_crores"]].sum().reset_index(),
        "worldwide_by_language": data.groupby(["language"])[["worldwide_collection_in_crores"]].sum().reset_index(),
        "directors_by_language": data.groupby(["language"])[["director"]].count().rename(columns={"director": "directors"}).reset_index(),
    }


def director_metrics(data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    top_by_films = data.groupby(["director"])[["title"]].count().sort_values("title", ascending=False).head(10).reset_index()
    if "worldwide_collection_in_crores" in data.columns:
        top_by_worldwide = (
            data.groupby(["director"])[["worldwide_collection_in_crores"]]
            .sum()
            .sort_values("worldwide_collection_in_crores", ascending=False)
            .head(10)
            .reset_index()
        )
    else:
        top_by_worldwide = pd.DataFrame()
    return {"top_by_films": top_by_films, "top_by_worldwide": top_by_worldwide}


def actor_metrics(data: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    key = "lead_actor_actress" if "lead_actor_actress" in data.columns else "lead_actor/actress"
    if key not in data.columns:
        raise ValueError("Lead actor column not found")
    return (
        data.groupby([key])["worldwide_collection_in_crores"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={key: "lead_actor_actress"})
    )


def runtime_extremes(data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    longest = data[["title", "runtime_mins"]].sort_values("runtime_mins", ascending=False).head(5).reset_index(drop=True)
    shortest = data[["title", "runtime_mins"]].sort_values("runtime_mins", ascending=True).head(5).reset_index(drop=True)
    return {"longest": longest, "shortest": shortest}


def industry_top(data: pd.DataFrame, industry: str, metric: str = "worldwide", n: int = 7) -> pd.DataFrame:
    sub = data[data["industry"].str.lower() == industry.lower()]
    return top_films(sub, metric=metric, n=n)


def not_overseas(data: pd.DataFrame) -> pd.DataFrame:
    return data[data["overseas_collection_in_crores"].fillna(0) == 0][["title"]].reset_index(drop=True)


def language_year_count(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby(["language", "year"])[["title"]].count().rename(columns={"title": "count"}).reset_index()


def ott_metrics(data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    if "ott_platform" not in data.columns:
        return {"by_ott": pd.DataFrame(), "by_language_ott": pd.DataFrame()}
    by_ott = data.groupby(["ott_platform"])[["title"]].count().rename(columns={"title": "count"}).reset_index()
    by_lang_ott = (
        data.groupby(["language", "ott_platform"])[["title"]].count().rename(columns={"title": "count"}).reset_index()
    )
    return {"by_ott": by_ott, "by_language_ott": by_lang_ott}


# -------------------------
# Export helpers
# -------------------------

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def export_table(df: pd.DataFrame, outdir: str, name: str):
    ensure_dir(outdir)
    csv_path = os.path.join(outdir, f"{name}.csv")
    md_path = os.path.join(outdir, f"{name}.md")
    df.to_csv(csv_path, index=False)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(df.to_markdown(index=False))


def build_report(outdir: str):
    sections = []
    for name in [
        "totals",
        "top_worldwide",
        "top_india",
        "top_overseas",
        "top_firstday",
        "year_counts",
        "language_budget",
        "language_worldwide",
        "directors_top_films",
        "directors_top_worldwide",
        "actors_top_worldwide",
        "runtime_longest",
        "runtime_shortest",
    ]:
        md = os.path.join(outdir, f"{name}.md")
        if os.path.exists(md):
            with open(md, "r", encoding="utf-8") as f:
                sections.append("\n\n## " + name.replace('_',' ').title() + "\n\n" + f.read())
    if sections:
        with open(os.path.join(outdir, "REPORT.md"), "w", encoding="utf-8") as f:
            f.write("# Movie Box Office Analytics – Report\n" + "".join(sections))


# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(description="Movie Box Office Analytics (Pandas)")
    parser.add_argument("command", nargs="?", default="report",
                        help=(
                            "Command: totals | top-films | counts-by | language-metrics | director-metrics | "
                            "actor-metrics | runtime | industry-top | not-overseas | language-year | ott-metrics | report"
                        ))
    parser.add_argument("positional", nargs="*")

    parser.add_argument("--input-dir", default=".")
    parser.add_argument("--fact", default=DEF_FACT)
    parser.add_argument("--director", default=DEF_DIR)
    parser.add_argument("--genre", default=DEF_GEN)
    parser.add_argument("--language", default=DEF_LANG)

    parser.add_argument("--export", action="store_true")
    parser.add_argument("--output-dir", default="output")

    parser.add_argument("--metric", default="worldwide", help="Metric for top-films: worldwide|india|overseas|firstday")
    parser.add_argument("--n", type=int, default=10, help="Top N rows")
    parser.add_argument("--by", default="year", help="counts-by: year|weekday")
    parser.add_argument("--industry", default="Bollywood")

    args = parser.parse_args()

    data, _ = load_data(args.input_dir, args.fact, args.director, args.genre, args.language)

    cmd = args.command.lower()
    outdir = args.output_dir

    if cmd == "totals":
        df = totals(data)
        print(df.to_string(index=False))
        if args.export:
            export_table(df, outdir, "totals")

    elif cmd == "top-films":
        df = top_films(data, metric=args.metric, n=args.n)
        print(df.to_string(index=False))
        if args.export:
            suffix_map = {"worldwide":"top_worldwide","india":"top_india","overseas":"top_overseas","firstday":"top_firstday"}
            suffix = suffix_map.get(args.metric, "top_worldwide")
            export_table(df, outdir, suffix)

    elif cmd == "counts-by":
        df = counts_by(data, by=args.by)
        print(df.to_string(index=False))
        if args.export:
            export_table(df, outdir, f"{args.by}_counts")

    elif cmd == "language-metrics":
        res = language_metrics(data)
        for name, df in res.items():
            print("\n## " + name + "\n")
            print(df.to_string(index=False))
            if args.export:
                export_table(df, outdir, name)

    elif cmd == "director-metrics":
        res = director_metrics(data)
        for name, df in res.items():
            print("\n## " + name + "\n")
            print(df.to_string(index=False))
            if args.export:
                export_table(df, outdir, f"directors_{name}")

    elif cmd == "actor-metrics":
        df = actor_metrics(data, n=args.n)
        print(df.to_string(index=False))
        if args.export:
            export_table(df, outdir, "actors_top_worldwide")

    elif cmd == "runtime":
        res = runtime_extremes(data)
        for name, df in res.items():
            print("\n## " + name + "\n")
            print(df.to_string(index=False))
            if args.export:
                export_table(df, outdir, f"runtime_{name}")

    elif cmd == "industry-top":
        df = industry_top(data, industry=args.industry, metric=args.metric, n=args.n)
        print(df.to_string(index=False))
        if args.export:
            export_table(df, outdir, f"{args.industry.lower()}_top_{args.metric}")

    elif cmd == "not-overseas":
        df = not_overseas(data)
        print(df.to_string(index=False))
        if args.export:
            export_table(df, outdir, "not_overseas")

    elif cmd == "language-year":
        df = language_year_count(data)
        print(df.to_string(index=False))
        if args.export:
            export_table(df, outdir, "language_year_counts")

    elif cmd == "ott-metrics":
        res = ott_metrics(data)
        for name, df in res.items():
            print("\n## " + name + "\n")
            if df.empty:
                print("(no ott_platform column)")
            else:
                print(df.to_string(index=False))
                if args.export:
                    export_table(df, outdir, name)

    elif cmd == "report":
        # Run a default set and export, then stitch REPORT.md
        export_table(totals(data), outdir, "totals")
        export_table(top_films(data, "worldwide", 10), outdir, "top_worldwide")
        export_table(top_films(data, "india", 10), outdir, "top_india")
        export_table(top_films(data, "overseas", 10), outdir, "top_overseas")
        export_table(top_films(data, "firstday", 10), outdir, "top_firstday")
        export_table(counts_by(data, "year"), outdir, "year_counts")
        lm = language_metrics(data)
        export_table(lm["budget_by_language"], outdir, "language_budget")
        export_table(lm["worldwide_by_language"], outdir, "language_worldwide")
        dm = director_metrics(data)
        export_table(dm["top_by_films"], outdir, "directors_top_films")
        export_table(dm["top_by_worldwide"], outdir, "directors_top_worldwide")
        export_table(actor_metrics(data, 10), outdir, "actors_top_worldwide")
        rt = runtime_extremes(data)
        export_table(rt["longest"], outdir, "runtime_longest")
        export_table(rt["shortest"], outdir, "runtime_shortest")
        build_report(outdir)
        print(f"Report generated under: {outdir}")

    else:
        raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
