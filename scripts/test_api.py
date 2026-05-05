import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# -------------------------
# CONFIG
# -------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
headers = {"X-Riot-Token": API_KEY}

# -------------------------
# LOAD CORRECT FILE
# -------------------------
CSV_FILE = "matches_safe.csv"

if not os.path.exists(CSV_FILE):
    print("❌ Fichier introuvable:", CSV_FILE)
    print("📂 Fichiers disponibles:")
    print(os.listdir())
    exit()

df = pd.read_csv(CSV_FILE)

if "matchId" not in df.columns:
    print("❌ colonne matchId introuvable")
    print(df.columns)
    exit()

match_ids = df["matchId"].dropna().unique()

print(f"🎮 Matches trouvés: {len(match_ids)}")

# -------------------------
# SAFE API CALL (Riot protection)
# -------------------------
def safe_get(url):
    for _ in range(8):
        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            return r.json()

        if r.status_code in [429, 409]:
            print("⏳ rate limit → sleep 10s")
            time.sleep(10)
            continue

        print("❌ API error:", r.status_code)
        time.sleep(2)

    return None

# -------------------------
# PROCESS DATASET
# -------------------------
dataset = []
skipped = 0

for i, match_id in enumerate(match_ids):

    print(f"\n[{i+1}/{len(match_ids)}] {match_id}")

    # MATCH DATA
    match_url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"
    match = safe_get(match_url)

    if not match:
        skipped += 1
        continue

    info = match["info"]
    duration = info.get("gameDuration", 0)

    win_100 = None
    for t in info["teams"]:
        if t["teamId"] == 100:
            win_100 = int(t["win"])

    # TIMELINE
    timeline_url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    timeline = safe_get(timeline_url)

    if not timeline:
        skipped += 1
        continue

    frames = timeline["info"]["frames"]

    # SAFE 15 MIN FRAME (FIX StopIteration)
    frame_15 = None
    for f in frames:
        if f["timestamp"] >= 900000:
            frame_15 = f
            break

    if not frame_15:
        skipped += 1
        continue

    # -------------------------
    # TEAM STATS
    # -------------------------
    teams = {
        100: {"gold": 0, "kills": 0, "cs": 0, "dragons": 0, "heralds": 0, "towers": 0},
        200: {"gold": 0, "kills": 0, "cs": 0, "dragons": 0, "heralds": 0, "towers": 0}
    }

    # GOLD + CS
    for pid, p in frame_15["participantFrames"].items():
        pid = int(pid)
        team = 100 if pid <= 5 else 200

        teams[team]["gold"] += p.get("totalGold", 0)
        teams[team]["cs"] += p.get("minionsKilled", 0) + p.get("jungleMinionsKilled", 0)

    # EVENTS
    for frame in frames:
        if frame["timestamp"] > 900000:
            break

        for e in frame["events"]:

            if e["type"] == "CHAMPION_KILL":
                killer = e.get("killerId", 0)
                if killer:
                    team = 100 if killer <= 5 else 200
                    teams[team]["kills"] += 1

            if e["type"] == "ELITE_MONSTER_KILL":
                killer = e.get("killerId", 0)
                team = 100 if killer <= 5 else 200

                if e["monsterType"] == "DRAGON":
                    teams[team]["dragons"] += 1

                if e["monsterType"] == "RIFTHERALD":
                    teams[team]["heralds"] += 1

            if e["type"] == "BUILDING_KILL":
                killer = e.get("killerId", 0)
                team = 100 if killer <= 5 else 200
                teams[team]["towers"] += 1

    # -------------------------
    # ROW FINAL
    # -------------------------
    dataset.append({
        "matchId": match_id,
        "duration": duration,
        "win_100": win_100,

        "gold_100": teams[100]["gold"],
        "gold_200": teams[200]["gold"],

        "kills_100": teams[100]["kills"],
        "kills_200": teams[200]["kills"],

        "cs_100": teams[100]["cs"],
        "cs_200": teams[200]["cs"],

        "dragons_100": teams[100]["dragons"],
        "dragons_200": teams[200]["dragons"],

        "heralds_100": teams[100]["heralds"],
        "heralds_200": teams[200]["heralds"],

        "towers_100": teams[100]["towers"],
        "towers_200": teams[200]["towers"],
    })

    time.sleep(0.6)

# -------------------------
# SAVE CSV
# -------------------------
out = pd.DataFrame(dataset)
out.to_csv("lol_ml_dataset.csv", index=False)

print("\n✅ DONE")
print("Saved rows:", len(out))
print("Skipped:", skipped)