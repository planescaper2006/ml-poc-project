import requests
import os
from dotenv import load_dotenv

# -------------------------
# CONFIG
# -------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")

headers = {
    "X-Riot-Token": API_KEY
}

# 👉 mets ton match ici
MATCH_ID = "EUW1_7839358932"

# -------------------------
# GET TIMELINE
# -------------------------
url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{MATCH_ID}/timeline"

r = requests.get(url, headers=headers)

if r.status_code != 200:
    print("❌ erreur API:", r.status_code)
    print(r.json())
    exit()

timeline = r.json()

# -------------------------
# COLLECT EVENTS
# -------------------------
event_types = set()
monster_types = set()
building_types = set()
ward_types = set()

frames = timeline["info"]["frames"]

for frame in frames:
    for e in frame["events"]:

        # type principal
        event_types.add(e["type"])

        # sous-types utiles
        if e["type"] == "ELITE_MONSTER_KILL":
            monster_types.add(e.get("monsterType"))

        if e["type"] == "BUILDING_KILL":
            building_types.add(e.get("buildingType"))

        if "wardType" in e:
            ward_types.add(e.get("wardType"))

# -------------------------
# PRINT RESULT
# -------------------------
print("\n🎯 EVENT TYPES:")
for t in sorted(event_types):
    print("-", t)

print("\n🐉 MONSTER TYPES:")
for t in sorted(monster_types):
    print("-", t)

print("\n🏰 BUILDING TYPES:")
for t in sorted(building_types):
    print("-", t)

print("\n👁️ WARD TYPES:")
for t in sorted(ward_types):
    print("-", t)