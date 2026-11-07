# GNSS Interference Map

**Live map:** https://sharaththebest.github.io/gnss-interference-map/

Mapping where aircraft over Europe and the Middle East lose reliable GPS, using only open ADS-B data.

## How it works

Aircraft broadcast a Navigation Integrity Category (NIC) with their position. When GNSS is jammed, NIC drops. This project parses one full day of global aircraft traces from [adsb.lol](https://adsb.lol), aggregates them on an H3 hexagon grid, and produces two views:

1. **Affected aircraft:** share of aircraft in each cell reporting degraded GPS (NIC < 7).
2. **Where GPS is lost:** cells where an aircraft's NIC drops from good to degraded within 2 minutes.

## Why two views

Aircraft often keep reporting degraded accuracy for many minutes after leaving a jammed area. In the "affected" view this creates long trails along flight routes, far from the interference source. The "onset" view counts only the moment GPS is lost, which removes these trails and points closer to where interference begins. On 1 November 2026, the onset view removed the broad band over Germany, Denmark and Hungary, while hotspots around the Baltic, the Black Sea, the Caucasus and the Eastern Mediterranean remained.

## Pipeline

- `pipeline/parse.py`: reads adsb.lol trace files, extracts NIC per position (above 5,000 ft, ADS-B only, NIC trusted for 60 s), detects onset events.
- `pipeline/aggregate.py`: per H3 cell (resolution 4), counts aircraft, degraded aircraft and onsets, with a minimum of 20 aircraft per cell.
- `web/`: MapLibre GL + deck.gl map, hosted on GitHub Pages.

Stack: Python, orjson, H3, DuckDB, pandas, MapLibre GL JS, deck.gl.

## Run it yourself

1. Download a day from [adsblol/globe_history_2026 releases](https://github.com/adsblol/globe_history_2026/releases) and extract it.
2. Set `DATA_DIR` in both pipeline scripts to your data folder.
3. `python pipeline/parse.py 2026-11-01` then `python pipeline/aggregate.py 2026-11-01`
4. `python -m http.server 8000` and open `http://localhost:8000/web/`

## Limitations

- Low NIC can also come from avionics faults, not only interference.
- Coverage depends on volunteer receivers; closed airspace (Ukraine, Belarus, parts of Russia) has no data.
- Onset cells mark where aircraft enter an interference footprint along flight routes, not the transmitter location.
- Open-data analysis for research and education, not an official or operational product.

## Credits

Data: [adsb.lol](https://adsb.lol), licensed under ODbL, contributed by volunteer feeders. Inspired by [GPSJam](https://gpsjam.org). Basemap: CARTO, OpenStreetMap contributors.

Author: Sharath Sunil Ravi, M.Sc. Remote Sensing and Geoinformatics, Karlsruhe Institute of Technology (KIT), Germany.
