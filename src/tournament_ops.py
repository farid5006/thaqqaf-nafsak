"""موديول عمليات البطولات: الاستعلام، إسناد المباريات، وحذف البطولات والمباريات وسجلاتها."""
import os
from typing import Any, Dict, List
try:
    from . import bank_storage
    from .tournament_manager import _get_tournaments_path, get_active_tournament, set_active_tournament
except ImportError:
    import bank_storage
    from tournament_manager import _get_tournaments_path, get_active_tournament, set_active_tournament

def get_matches_for_tournament(tour_name: str) -> List[Dict[str, Any]]:
    matches = bank_storage.load_matches_history()
    clean = tour_name.strip()
    return [m for m in matches if (m.get("tournament") or "").strip() == clean]

def assign_match_to_tournament(match_id: str, new_tour: str) -> bool:
    matches = bank_storage.load_matches_history()
    found = False
    for m in matches:
        if str(m.get("match_id", "")) == str(match_id):
            m["tournament"] = new_tour.strip()
            found = True; break
    if found:
        bank_storage.save_json_file(matches, os.path.join(bank_storage.get_data_dir(), "matches_history.json"))
    return found

def _purge_used_questions(deleted_match_ids: set) -> None:
    bank = bank_storage.load_bank()
    used = bank.get("used", {})
    new_used = {}
    for qid, val in used.items():
        mid = val.get("match_id") if isinstance(val, dict) else str(val)
        if str(mid) not in deleted_match_ids:
            new_used[qid] = val
    bank["used"] = new_used
    bank_storage.save_bank(bank)

def delete_tournament(tour_name: str, reset_questions: bool = False) -> bool:
    clean = tour_name.strip()
    t_path = _get_tournaments_path()
    t_data = bank_storage.load_json_file(t_path, {})
    hist = t_data.get("history", [])
    if clean not in hist: return False

    hist.remove(clean)
    if not hist: hist.append("بطولة 1")
    t_data["history"] = hist
    if t_data.get("active") == clean: t_data["active"] = hist[0]
    bank_storage.save_json_file(t_data, t_path)

    matches = bank_storage.load_matches_history()
    del_ids = {str(m.get("match_id", "")) for m in matches if (m.get("tournament") or "").strip() == clean}
    kept = [m for m in matches if (m.get("tournament") or "").strip() != clean]
    bank_storage.save_json_file(kept, os.path.join(bank_storage.get_data_dir(), "matches_history.json"))

    if reset_questions and del_ids:
        _purge_used_questions(del_ids)
    return True

def delete_match(match_id: str, reset_questions: bool = False) -> bool:
    mid_str = str(match_id).strip()
    matches = bank_storage.load_matches_history()
    kept = [m for m in matches if str(m.get("match_id", "")).strip() != mid_str]
    if len(kept) == len(matches): return False
    bank_storage.save_json_file(kept, os.path.join(bank_storage.get_data_dir(), "matches_history.json"))
    if reset_questions:
        _purge_used_questions({mid_str})
    return True
