"""Download all major T20 league datasets from Cricsheet."""

import io
import json
import os
import urllib.request
import zipfile

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
BASE_URL = "https://cricsheet.org/downloads"

LEAGUES = {
    "ipl": "ipl_json.zip",
    "bbl": "bbl_json.zip",
    "cpl": "cpl_json.zip",
    "psl": "psl_json.zip",
    "lpl": "lpl_json.zip",
    "sa20": "sat_json.zip",
    "the_hundred": "mct_json.zip",
    "bpl": "bpl_json.zip",
    "mlc": "mlc_json.zip",
    "t20i": "it20s_male_json.zip",
    "ilt20": "ilt_json.zip",
    "npl": "npl_json.zip",
}


def download_league(league_id, filename):
    league_dir = os.path.join(RAW_DIR, league_id)
    os.makedirs(league_dir, exist_ok=True)

    # Skip if already has files
    existing = [f for f in os.listdir(league_dir) if f.endswith(".json")]
    if len(existing) > 10:
        print(f"  {league_id}: already has {len(existing)} files, skipping")
        return len(existing)

    url = f"{BASE_URL}/{filename}"
    print(f"  Downloading {league_id} from {url} ...")
    response = urllib.request.urlopen(url)
    data = response.read()
    size_mb = len(data) / 1024 / 1024

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        json_files = [f for f in zf.namelist() if f.endswith(".json")]
        for name in json_files:
            target = os.path.join(league_dir, os.path.basename(name))
            with zf.open(name) as src, open(target, "wb") as dst:
                dst.write(src.read())

    count = len([f for f in os.listdir(league_dir) if f.endswith(".json")])
    print(f"  {league_id}: {count} matches ({size_mb:.1f} MB)")
    return count


def migrate_existing_ipl():
    """Move existing IPL files from data/raw/ to data/raw/ipl/."""
    ipl_dir = os.path.join(RAW_DIR, "ipl")
    os.makedirs(ipl_dir, exist_ok=True)

    existing_in_ipl = [f for f in os.listdir(ipl_dir) if f.endswith(".json")]
    if len(existing_in_ipl) > 10:
        return  # Already migrated

    moved = 0
    for f in os.listdir(RAW_DIR):
        if f.endswith(".json"):
            src = os.path.join(RAW_DIR, f)
            dst = os.path.join(ipl_dir, f)
            os.rename(src, dst)
            moved += 1

    if moved:
        print(f"  Migrated {moved} existing IPL files to data/raw/ipl/")


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    # First migrate existing flat IPL files into subfolder
    print("Migrating existing IPL data...")
    migrate_existing_ipl()

    total = 0
    print("\nDownloading all leagues:")
    for league_id, filename in LEAGUES.items():
        try:
            count = download_league(league_id, filename)
            total += count
        except Exception as e:
            print(f"  {league_id}: FAILED - {e}")

    print(f"\nDone! Total: {total} match files across {len(LEAGUES)} leagues")

    # Summary
    print("\nPer-league breakdown:")
    for league_id in LEAGUES:
        league_dir = os.path.join(RAW_DIR, league_id)
        if os.path.isdir(league_dir):
            count = len([f for f in os.listdir(league_dir) if f.endswith(".json")])
            print(f"  {league_id:15s}  {count:5d} matches")


if __name__ == "__main__":
    main()
