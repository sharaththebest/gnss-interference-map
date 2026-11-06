"""Score each hex cell: share of degraded aircraft + GPS-loss onsets."""
import sys, duckdb, h3

DATA_DIR = "/Volumes/Sharath HD/gnss-data"
DAY = sys.argv[1] if len(sys.argv) > 1 else "2026-11-01"
MIN_AIRCRAFT = 20

pts = f"{DATA_DIR}/processed/points_{DAY}.parquet"
ons = f"{DATA_DIR}/processed/onsets_{DAY}.parquet"
df = duckdb.sql(f"""
    WITH per_aircraft AS (
        SELECT icao, cell, SUM(n_bad)::DOUBLE / SUM(n_points) AS bad_share
        FROM read_parquet('{pts}') GROUP BY icao, cell
    ),
    affected AS (
        SELECT cell, COUNT(*) AS n_aircraft,
               SUM(CASE WHEN bad_share > 0.5 THEN 1 ELSE 0 END)::INT AS n_bad
        FROM per_aircraft GROUP BY cell HAVING COUNT(*) >= {MIN_AIRCRAFT}
    ),
    onset AS (
        SELECT cell, COUNT(DISTINCT icao) AS n_onset
        FROM read_parquet('{ons}') GROUP BY cell
    )
    SELECT a.*, COALESCE(o.n_onset, 0)::INT AS n_onset
    FROM affected a LEFT JOIN onset o USING (cell)
""").df()

df["pct_bad"] = (100 * df.n_bad / df.n_aircraft).round(1)
df["onset_rate"] = (100 * df.n_onset / df.n_aircraft).round(2)
df["lat"], df["lon"] = zip(*df.cell.map(h3.cell_to_latlng))

cols = ["cell", "n_aircraft", "n_bad", "pct_bad", "n_onset", "onset_rate"]
df[cols].to_json(f"data/{DAY}.json", orient="records")

print(f"{len(df)} cells saved to data/{DAY}.json")
print(f"Total onset events in scored cells: {df.n_onset.sum()}")
print(f"Cells with >= 3 onsets: {(df.n_onset >= 3).sum()}\n")
print("onset_rate distribution (cells with >= 3 onsets):")
print(df[df.n_onset >= 3].onset_rate.describe().round(2).to_string(), "\n")
print("Top 20 cells by onset rate (min 3 onsets):")
print(df[df.n_onset >= 3].sort_values("onset_rate", ascending=False).head(20)
        [["lat", "lon", "n_aircraft", "n_onset", "onset_rate", "pct_bad"]]
        .round(2).to_string(index=False))
