"""موديول إدارة البطولات وسجلات المسابقات وتجميع المباريات القديمة تلقائياً."""
import os
from typing import Any, Dict, List
try:
    from . import bank_storage
except ImportError:
    import bank_storage

def _get_tournaments_path() -> str:
    return os.path.join(bank_storage.get_data_dir(), "tournament_info.json")

def ensure_legacy_matches_grouped() -> str:
    """تجميع كافة المباريات السابقة غير المصنفة تحت بطولة 1 وتاريخ أول مباراة."""
    matches = bank_storage.load_matches_history()
    t_path = _get_tournaments_path()
    t_data = bank_storage.load_json_file(t_path, {})
    default_name = "بطولة 1"
    if matches:
        date_str = str(matches[0].get("date", "")).strip()
        parts = date_str.split()
        first_date = parts[0].replace("/", "-") if parts else ""
        if first_date: default_name = f"بطولة 1 ({first_date})"

    updated = False
    for m in matches:
        cur_t = (m.get("tournament") or "").strip()
        if not cur_t or cur_t == "البطولة الأولى":
            m["tournament"] = default_name
            updated = True

    if updated:
        bank_storage.save_json_file(matches, os.path.join(bank_storage.get_data_dir(), "matches_history.json"))

    hist = t_data.get("history", [])
    if default_name not in hist: hist.insert(0, default_name)
    if not t_data.get("active") or t_data.get("active") == "البطولة الأولى":
        t_data["active"] = default_name
    t_data["history"] = [t for t in hist if t != "البطولة الأولى"]
    bank_storage.save_json_file(t_data, t_path)
    return t_data.get("active", default_name)

def get_active_tournament() -> str:
    ensure_legacy_matches_grouped()
    data = bank_storage.load_json_file(_get_tournaments_path(), {})
    return data.get("active", "بطولة 1")

def set_active_tournament(name: str) -> None:
    ensure_legacy_matches_grouped()
    data = bank_storage.load_json_file(_get_tournaments_path(), {})
    clean = name.strip() or "بطولة 1"
    data["active"] = clean
    hist = data.setdefault("history", [])
    if clean not in hist: hist.append(clean)
    bank_storage.save_json_file(data, _get_tournaments_path())

def start_new_tournament(name: str) -> str:
    clean = name.strip() or "بطولة جديدة"
    set_active_tournament(clean)
    return clean

def list_tournaments() -> List[str]:
    ensure_legacy_matches_grouped()
    data = bank_storage.load_json_file(_get_tournaments_path(), {})
    return data.get("history", ["بطولة 1"])
