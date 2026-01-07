import json
import os

BASE = "data"


def _load(name):
    path = f"{BASE}/{name}.json"
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(name, data):
    os.makedirs(BASE, exist_ok=True)
    with open(f"{BASE}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------- FAVORITES (USER BASED) ----------------

def add_favorite(user_id, track):
    data = _load("favorites")

    if not isinstance(data, dict):
        data = {}

    user_id = str(user_id)
    track_id = str(track["id"])

    if user_id not in data:
        data[user_id] = {}

    data[user_id][track_id] = {
        "id": track["id"],
        "name": track["name"],
        "artist_name": track["artist_name"],
        "audio": track["audio"],
        "image": track.get("image"),
        "duration": track.get("duration")
    }

    _save("favorites", data)


def is_favorite(user_id, track_id):
    data = _load("favorites")

    user_id = str(user_id)
    track_id = str(track_id)

    return (
        user_id in data and
        track_id in data[user_id]
    )
def remove_favorite(user_id, track_id):
    data = _load("favorites")

    if not isinstance(data, dict):
        return

    user_id = str(user_id)

    if user_id in data:
        data[user_id].pop(str(track_id), None)

    _save("favorites", data)



def get_favorites(user_id):
    data = _load("favorites")

    if not isinstance(data, dict):
        return []

    return list(data.get(str(user_id), {}).values())
