"""Parse one day of adsb.lol traces.
Output 1: (aircraft, cell, hour) counts of good/degraded positions.
Output 2: onset events, where an aircraft's GPS goes from good to degraded."""
import gzip, glob, os, sys
from multiprocessing import Pool
import orjson, h3, pandas as pd

DATA_DIR = "/Volumes/Sharath HD/gnss-data"
DAY = sys.argv[1] if len(sys.argv) > 1 else "2026-11-01"
H3_RES = 4
MIN_ALT_FT = 5000
NIC_BAD = 7
MAX_STALE_S = 60     # a NIC value is only trusted for 60 s
MAX_GAP_S = 120      # good->bad must happen within 2 min to count as onset

def parse_file(path):
    try:
        with open(path, "rb") as f:
            raw = f.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        d = orjson.loads(raw)
    except Exception:
        return [], []
    icao, t0 = d.get("icao"), d.get("timestamp", 0)
    nic, nic_t = None, None
    agg, onsets = {}, []
    for p in d.get("trace", []):
        if len(p) < 10:
            continue
        alt = p[3]
        airborne = isinstance(alt, (int, float)) and alt >= MIN_ALT_FT
        det = p[8]
        if isinstance(det, dict) and "nic" in det:
            new_nic = det["nic"]
            # onset: previous report good, this one bad, close in time
            if (nic is not None and nic >= NIC_BAD and new_nic < NIC_BAD
                    and p[0] - nic_t <= MAX_GAP_S
                    and p[9] == "adsb_icao" and airborne):
                cell = h3.latlng_to_cell(p[1], p[2], H3_RES)
                onsets.append((icao, cell, int((t0 + p[0]) // 3600), p[1], p[2]))
            nic, nic_t = new_nic, p[0]
        if p[9] != "adsb_icao" or nic is None or not airborne:
            continue
        if p[0] - nic_t > MAX_STALE_S:
            continue
        cell = h3.latlng_to_cell(p[1], p[2], H3_RES)
        hour = int((t0 + p[0]) // 3600)
        a = agg.setdefault((cell, hour), [0, 0])
        a[0] += 1
        if nic < NIC_BAD:
            a[1] += 1
    counts = [(icao, c, h, n, b) for (c, h), (n, b) in agg.items()]
    return counts, onsets

def to_time(df):
    df["hour"] = pd.to_datetime(df["hour"] * 3600, unit="s", utc=True)
    return df

if __name__ == "__main__":
    src = f"{DATA_DIR}/raw/{DAY}/traces"
    files = [f for f in glob.glob(f"{src}/*/trace_full_*.json")
             if not os.path.basename(f).startswith("._")]
    print(f"{len(files)} files for {DAY}")
    counts, onsets = [], []
    with Pool() as pool:
        for i, (c, o) in enumerate(pool.imap_unordered(parse_file, files, chunksize=200)):
            counts.extend(c)
            onsets.extend(o)
            if i % 5000 == 0:
                print(f"  {i}/{len(files)}", flush=True)
    out = f"{DATA_DIR}/processed"
    to_time(pd.DataFrame(counts, columns=["icao", "cell", "hour", "n_points", "n_bad"])
            ).to_parquet(f"{out}/points_{DAY}.parquet", index=False)
    to_time(pd.DataFrame(onsets, columns=["icao", "cell", "hour", "lat", "lon"])
            ).to_parquet(f"{out}/onsets_{DAY}.parquet", index=False)
    print(f"Saved {len(counts):,} count rows and {len(onsets):,} onset events")
