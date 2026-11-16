"""موديول إدارة البطولات وسجلات المسابقات وتجميع المباريات."""
import os
from typing import Any, Dict, List
try:
    from .bank_storage import get_data_dir, load_json_file, save_json_file, load_matches_history, save_match_history
except ImportError:
    from bank_storage import get_data_dir, load_json_file, save_json_file, load_matches_history, save_match_history

def _get_tournaments_path() -> str:
    return os.path.join(get_data_dir(), "tournament_info.json")

def get_active_tournament() -> str:
    data = load_json_file(_get_tournaments_path(), {"active": "البطولة الأولى", "history": ["البطولة الأولى"]})
    return data.get("active", "البطولة الأولى")

def set_active_tournament(name: str) -> None:
    data = load_json_file(_get_tournaments_path(), {"active": "البطولة الأولى", "history": ["البطولة الأولى"]})
    clean = name.strip() or "بطولة جديدة"
    data["active"] = clean
    hist = data.setdefault("history", [])
    if clean not in hist: hist.append(clean)
    save_json_file(data, _get_tournaments_path())

def start_new_tournament(name: str) -> str:
    """بدء بطولة جديدة وربط المباريات السابقة غير المربوطة بالبطولة السابقة."""
    clean = name.strip() or "بطولة جديدة"
    old_active = get_active_tournament()
    matches = load_matches_history()
    updated = False
    for m in matches:
        if not m.get("tournament"):
            m["tournament"] = old_active
            updated = True
    if updated:
        p = os.path.join(get_data_dir(), "matches_history.json")
        save_json_file(matches, p)
    set_active_tournament(clean)
    return clean

def list_tournaments() -> List[str]:
    data = load_json_file(_get_tournaments_path(), {"active": "البطولة الأولى", "history": ["البطولة الأولى"]})
    return data.get("history", ["البطولة الأولى"])
