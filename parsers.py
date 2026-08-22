import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional

def parse_stardew_valley(file_path: Path) -> Dict[str, Any]:
    """Parse Stardew Valley save file to extract player stats."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except (ET.ParseError, PermissionError):
        raise ValueError(f"Failed to parse XML in {file_path}")

    player = root.find("player")
    if player is None:
        raise ValueError("No 'player' node found in Stardew save")

    name = player.findtext("name", "Unknown")
    money = int(player.findtext("money", "0"))
    
    day = root.findtext("dayOfMonth", "1")
    season = root.findtext("currentSeason", "spring")
    year = root.findtext("year", "1")
    
    season_str = season.capitalize() if season else "Spring"
    in_game_date = f"Year {year}, {season_str} {day}"
    
    try:
        yr_val = max(1, int(year))
        day_val = max(1, int(day))
    except ValueError:
        yr_val, day_val = 1, 1

    # print(f"DEBUG: stardew player={name} money={money} season={season}")
    
    seasons = ["spring", "summer", "fall", "winter"]
    season_idx = 0
    if season:
        try:
            season_idx = seasons.index(season.lower())
        except ValueError:
            pass

    total_days = ((yr_val - 1) * 112) + (season_idx * 28) + day_val

    return {
        "player_name": name,
        "currency": money,
        "in_game_time": in_game_date,
        "raw_days": total_days
    }

def parse_rimworld(file_path: Path) -> Dict[str, Any]:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except (ET.ParseError, PermissionError):
        raise ValueError(f"Failed to parse RimWorld save XML {file_path}")

    # Find colony name and tick counts deeper in the save tree
    colony_name = root.findtext(".//colonyInfo/colonyName", "Unnamed Colony")
    if colony_name == "Unnamed Colony":
        # Fallback for older rimworld save versions
        faction_name = root.findtext(".//faction/name")
        if faction_name:
            colony_name = faction_name

    # playTicks represents the absolute game time elapsed
    ticks_str = root.findtext(".//playTicks", "0")
    try:
        ticks = int(ticks_str)
    except ValueError:
        ticks = 0

    # 1 Rimworld day is 60,000 game ticks
    playTime_hours = round(ticks / 2500, 1)
    days_elapsed = int(ticks / 60000)

    return {
        "player_name": colony_name,
        "currency": 0,  # Silver is inventory-based, not stored as a single global value
        "in_game_time": f"Day {days_elapsed} ({playTime_hours} hrs)",
        "raw_days": days_elapsed
    }

def parse_json_save(file_path: Path) -> Dict[str, Any]:
    # Fallback parser for generic JSON-based saves
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        raise ValueError(f"Failed to parse JSON file {file_path}")

    # Look for common properties inside arbitrary JSON save structures
    possible_names = ["playerName", "player_name", "name", "profile_name", "character"]
    possible_gold = ["gold", "money", "currency", "credits", "shards"]
    possible_days = ["day", "days", "days_played", "in_game_days"]

    def search_keys(d: Any, targets: list) -> Optional[Any]:
        if isinstance(d, dict):
            for k, v in d.items():
                if k.lower() in targets:
                    return v
                res = search_keys(v, targets)
                if res is not None:
                    return res
        elif isinstance(d, list):
            for item in d:
                res = search_keys(item, targets)
                if res is not None:
                    return res
        return None

    p_name = str(search_keys(data, possible_names) or "Unknown Player")
    gold_val = search_keys(data, possible_gold)
    days_val = search_keys(data, possible_days)

    try:
        currency = int(gold_val) if gold_val is not None else 0
    except (ValueError, TypeError):
        currency = 0

    try:
        days = int(days_val) if days_val is not None else 0
    except (ValueError, TypeError):
        days = 0

    return {
        "player_name": p_name,
        "currency": currency,
        "in_game_time": f"Day {days}" if days > 0 else "Unknown Time",
        "raw_days": days
    }
