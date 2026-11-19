"""Download the open GTFS bus feeds used in this project to data/raw/<city>/  (needs internet).

    python download_data.py                  # all cities in FEEDS
    python download_data.py pune kochi       # selected cities
    python download_data.py --url https://example.com/feed.zip --name mycity

The Lepton Software dataset named in the project document (Datarade) is a paid listing and could not be obtained, so these open feeds are used.
Raw data is NOT committed to Git; this script recreates it. If a URL fails (403 / 404), open the feed page, download the ZIP manually
and place it in data/raw/<city>/ - every script accepts the ZIP directly.
Not available as open GTFS: Mumbai (BEST), Rajkot, Hubli-Dharwad; Delhi's official feed needs an API key (https://otd.delhi.gov.in).
"""
import argparse, os, sys, zipfile
import requests

MDB = "https://files.mobilitydatabase.org/{id}/latest.zip"
FEEDS = {  # city -> candidate URLs, tried in order
    "ahmedabad": ["https://github.com/croyla/amd-gtfs/raw/main/gtfs.zip"],                                        # AMTS + Janmarg BRTS (community feed)
    "bengaluru": ["https://github.com/Vonter/bmtc-gtfs/raw/main/gtfs/bmtc.zip"],                                  # BMTC (unofficial community feed)
    "chennai": ["https://raw.githubusercontent.com/ungalsoththu/ChennaiGTFS/main/data/chennai-unified-gtfs.zip"],  # unified feed, MobilityDatabase mdb-3360
    "delhi": ["https://raw.githubusercontent.com/transitland/gtfs-archives-not-hosted-elsewhere/3db26c0092b6efeb1886a99b4fc0765122b0282b/delhi-bus.zip"],  # archived DTC feed (2022-24)
    "hyderabad": [MDB.format(id="mdb-3361")],                                                                     # TGSRTC
    "kochi": ["https://jungle-bus.github.io/KochiTransport/KochiTransport.zip", MDB.format(id="mdb-1835")],       # buses + boats
    "pune": [MDB.format(id="mdb-3137")],                                                                          # PMPML
}
REQUIRED = {"routes.txt", "trips.txt", "stop_times.txt", "stops.txt"}


def fetch(url, dest):
    r = requests.get(url, timeout=180, stream=True, headers={"User-Agent": "RouteRanker/1.0"})
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)
    with zipfile.ZipFile(dest) as z:               # validate: a real GTFS zip with the required files
        names = {n.split("/")[-1] for n in z.namelist()}
    if not REQUIRED <= names:
        raise ValueError(f"ZIP is missing {sorted(REQUIRED - names)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cities", nargs="*")
    ap.add_argument("--url")
    ap.add_argument("--name")
    a = ap.parse_args()
    jobs = {a.name or "custom": [a.url]} if a.url else {c: FEEDS[c] for c in (a.cities or FEEDS)}
    for city, urls in jobs.items():
        d = os.path.join("data", "raw", city)
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, f"{city}_gtfs.zip")
        for u in urls:
            try:
                print(f"[{city}] {u}")
                fetch(u, dest)
                print(f"  OK -> {dest}")
                break
            except Exception as e:
                print(f"  failed: {e}")
                if os.path.exists(dest):
                    os.remove(dest)                # never leave a broken download behind
        else:
            print(f"  !! could not download {city}. Download the ZIP manually into {d}/")


if __name__ == "__main__":
    sys.exit(main())
