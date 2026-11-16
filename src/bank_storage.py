import hashlib, json, os, re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

def normalize_text(text: str) -> str:
    t = re.sub(r"[\u064B-\u065F\u0670]", "", text or "")
    t = re.sub(r"[أإآ]", "ا", t)
    t = re.sub(r"[ة]", "ه", t)
    t = re.sub(r"[ى]", "ي", t)
    t = re.sub(r"[؟?.,:!_\-؛]", " ", t)
    return " ".join(t.lower().split())

def compute_question_id(q_text: str, field: str = "") -> str:
    return hashlib.md5(normalize_text(q_text).encode("utf-8")).hexdigest()

def get_data_dir() -> str:
    appdata = os.environ.get("APPDATA")
    d = os.path.join(appdata, "nvda", "thaqqaf_nafsak_data") if appdata else os.path.join(os.path.expanduser("~"), ".thaqqaf_nafsak")
    os.makedirs(d, exist_ok=True); return d

def load_json_file(file_path: str, default: Any) -> Any:
    if not os.path.exists(file_path): return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            return json.loads(raw) if raw else default
    except Exception: return default

def save_json_file(data: Any, file_path: str) -> None:
    parent = os.path.dirname(os.path.abspath(file_path))
    if parent: os.makedirs(parent, exist_ok=True)
    tmp = f"{file_path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, file_path)

def load_bank(file_path: Optional[str] = None) -> Dict[str, Any]:
    p = file_path or os.path.join(get_data_dir(), "question_bank.json")
    b = load_json_file(p, {"questions": [], "used": {}, "file_path": ""})
    if not isinstance(b, dict): b = {"questions": [], "used": {}, "file_path": ""}
    b.setdefault("questions", []); b.setdefault("used", {}); b.setdefault("file_path", "")
    return b

def save_bank(bank_data: Dict[str, Any], file_path: Optional[str] = None) -> None:
    save_json_file(bank_data, file_path or os.path.join(get_data_dir(), "question_bank.json"))

def get_last_file_path() -> str: return load_bank().get("file_path", "")

def set_last_file_path(file_path: str) -> None:
    b = load_bank(); b["file_path"] = file_path; save_bank(b)

def get_unused_questions(bank_data: Dict[str, Any], round_key: str, field: Optional[str] = None) -> List[Dict[str, Any]]:
    used, q_list = bank_data.get("used", {}), bank_data.get("questions", [])
    if isinstance(q_list, list):
        return [q for q in q_list if (not round_key or q.get("round_key") == round_key) and (not field or q.get("field") == field) and q.get("id") not in used]
    return []

def mark_questions_used(bank_data: Dict[str, Any], q_ids: List[str], match_id: str) -> None:
    used = bank_data.setdefault("used", {})
    now = datetime.now(timezone.utc).isoformat()
    for q_id in q_ids: used[q_id] = {"match_id": match_id, "used_at": now}

def mark_question_used(bank_data: Dict[str, Any], q_id: str, match_id: str) -> None:
    mark_questions_used(bank_data, [q_id], match_id)

def save_match_history(match_summary: Dict[str, Any]) -> None:
    p = os.path.join(get_data_dir(), "matches_history.json")
    history = load_json_file(p, [])
    if not isinstance(history, list): history = []
    history.append(match_summary); save_json_file(history, p)

def load_matches_history() -> List[Dict[str, Any]]:
    h = load_json_file(os.path.join(get_data_dir(), "matches_history.json"), [])
    return h if isinstance(h, list) else []
