import gzip, json, glob, os

DATA = "/Volumes/Sharath HD/gnss-data/raw/2026-11-01"

files = [f for f in glob.glob(f"{DATA}/**/trace_full_*", recursive=True)
         if not os.path.basename(f).startswith("._")]
print(len(files), "trace files\n")

with open(files[0], "rb") as f:
    raw = f.read()
if raw[:2] == b"\x1f\x8b":
    raw = gzip.decompress(raw)
data = json.loads(raw)

print("File:", files[0])
print("Top-level keys:", list(data.keys()), "\n")
print("First 3 points:")
for p in data["trace"][:3]:
    print(p)

print("\nFirst details dictionary found:")
for p in data["trace"]:
    d = next((x for x in p if isinstance(x, dict)), None)
    if d:
        print(d)
        break
