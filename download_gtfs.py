
import os
import zipfile
import requests

DATA_DIR = "data/raw"

feeds = {
    "Hyderabad": "https://data.opencity.in/dataset/88e2d145-7ec6-4666-88dd-6cf18b18312e/resource/1b0d18bb-b2fb-4a79-8ed0-1e071da5790c/download/telangana_opendata_gtfs_tgsrtc_08_february_2026.zip",

    "Mumbai": "https://github.com/croyla/mumbai-gtfs/raw/refs/heads/main/gtfs_compat.zip",

    "Pune": "https://raw.githubusercontent.com/croyla/pmpml-gtfs/refs/heads/main/pmpml_gtfs_compat.zip",

    "Chennai": "https://raw.githubusercontent.com/ungalsoththu/ChennaiGTFS/main/data/chennai-unified-gtfs.zip",

    "Ahmedabad": "https://github.com/croyla/amd-gtfs/raw/refs/heads/main/gtfs_compat.zip",

    "Rajkot": "https://github.com/croyla/rrl-gtfs/raw/refs/heads/main/gtfs_compat.zip"
}

for city, url in feeds.items():
    folder = os.path.join(DATA_DIR, city)
    os.makedirs(folder, exist_ok=True)

    if os.path.exists(os.path.join(folder, "routes.txt")):
        print(city, "- Already downloaded. Skipping.")
        continue

    try:
        print("Downloading:", city)
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        zip_path = os.path.join(folder, "gtfs.zip")

        with open(zip_path, "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(folder)

        print(city, "- Download completed")

    except (requests.RequestException, zipfile.BadZipFile) as e:
        print(city, "- Download failed:", e)

print("\nDownload process finished!")
