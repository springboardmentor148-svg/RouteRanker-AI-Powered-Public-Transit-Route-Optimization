"""Download real Indian GTFS feeds to data/raw/<city>/  (run this on YOUR machine, needs internet).

    python download_data.py                 # all cities in FEEDS
    python download_data.py hyderabad pune  # selected cities
    python download_data.py --url https://example.com/feed.zip --name mycity

Primary source: MobilityDatabase (feed pages: https://mobilitydatabase.org/feeds/gtfs/<id>).
TGSRTC also publishes its own open data at https://tgsrtc.telangana.gov.in/open-data
If a URL below fails (403/404): open the feed page, click 'Download' and drop the ZIP into
data/raw/<city>/ — the app and pipeline accept ZIPs directly.
Add more cities by finding the feed id on https://mobilitydatabase.org/feeds?q=india
"""
import argparse, os, sys, zipfile
import requests

MDB = "https://files.mobilitydatabase.org/{id}/latest.zip"
FEEDS = {  # city -> list of candidate URLs (tried in order)
    # --- verified: downloaded + processed successfully by this project ---
    "chennai": ["https://raw.githubusercontent.com/ungalsoththu/ChennaiGTFS/main/data/chennai-unified-gtfs.zip"],  # = mdb-3360, ~3,900 bus patterns
    "ahmedabad": ["https://github.com/croyla/amd-gtfs/raw/main/gtfs.zip"],                                         # AMTS + Janmarg BRTS
    # --- verified working (Hyderabad/Pune/Kochi downloaded OK on the user's laptop) ---
    "hyderabad": [MDB.format(id="mdb-3361")],   # TGSRTC, 1,031 routes (also https://tgsrtc.telangana.gov.in/open-data)
    "pune": [MDB.format(id="mdb-3137")],        # PMPML, 309 routes
    "kochi": ["https://jungle-bus.github.io/KochiTransport/KochiTransport.zip", MDB.format(id="mdb-1835")],  # 473 bus+ferry routes (2022-23)
    "bengaluru": ["https://github.com/Vonter/bmtc-gtfs/raw/main/gtfs/bmtc.zip"],  # BMTC, 4,434 routes, unofficial but current (Namma BMTC app)
    "delhi": ["https://raw.githubusercontent.com/transitland/gtfs-archives-not-hosted-elsewhere/3db26c0092b6efeb1886a99b4fc0765122b0282b/delhi-bus.zip"],  # DTC, 2,964 routes (IIIT-Delhi, 2022-24)
    # Not available as open GTFS: Mumbai BEST, Rajkot, Hubli-Dharwad (search https://mobilitydatabase.org/feeds?q=india)
}


def fetch(url, dest):
    r = requests.get(url, timeout=120, stream=True, headers={"User-Agent": "RouteRanker/1.0"})
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)
    with zipfile.ZipFile(dest) as z:  # validate
        names = {n.split("/")[-1] for n in z.namelist()}
    need = {"routes.txt", "trips.txt", "stop_times.txt", "stops.txt"}
    if not need <= names:
        raise ValueError(f"ZIP is missing {need - names}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cities", nargs="*")
    ap.add_argument("--url"); ap.add_argument("--name")
    a = ap.parse_args()
    jobs = {a.name or "custom": [a.url]} if a.url else {
        c: FEEDS[c] for c in (a.cities or FEEDS)}
    for city, urls in jobs.items():
        d = os.path.join("data", "raw", city); os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, f"{city}_gtfs.zip")
        for u in urls:
            try:
                print(f"[{city}] {u}"); fetch(u, dest); print(f"  OK -> {dest}"); break
            except Exception as e:
                print(f"  failed: {e}")
        else:
            print(f"  !! could not download {city}. Download manually and place ZIP in {d}/")


if __name__ == "__main__":
    sys.exit(main())
