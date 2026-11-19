"""موديول بناء جداول وترتيب أسئلة الجولات الثلاث وإدارة المراحل وحفظ التقرير."""
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

def _get_qid(q: Dict[str, Any], field: str) -> str:
    try: from .bank_storage import compute_question_id
    except ImportError: from bank_storage import compute_question_id
    return q.get("id") or compute_question_id(q.get("question", ""), field)

def build_r1_queue(q_data: Dict[str, Any], team: str, opp: str, used: Set[str] = None, rep_pct: int = 0) -> List[Tuple[str, Dict[str, Any]]]:
    used_set, pools = (used or set()) if rep_pct < 100 else set(), {}
    for f, q_list in q_data.get("round_1", {}).items():
        av = [q for q in q_list if _get_qid(q, f) not in used_set]
        p = av if len(av) >= 2 else (av + [q for q in q_list if q not in av])
        if p: pools[f] = list(p)
    queue, pairs = [], 0
    while pairs < 12:
        added = False
        for f, p in pools.items():
            if pairs >= 12: break
            if len(p) >= 2:
                queue.extend([(team, p.pop(0)), (opp, p.pop(0))]); pairs += 1; added = True
        if not added: break
    if pairs < 12:
        rem = [p.pop(0) for p in pools.values() if p]
        while pairs < 12 and len(rem) >= 2:
            queue.extend([(team, rem.pop(0)), (opp, rem.pop(0))]); pairs += 1
    return queue

def build_r2_queue(q_data: Dict[str, Any], team: str, opp: str, f1: str, f2: str, used: Set[str] = None, rep_pct: int = 0) -> List[Tuple[str, Dict[str, Any]]]:
    used_set, r2 = (used or set()) if rep_pct < 100 else set(), q_data.get("round_2", {})
    if f1 == f2:
        qs = r2.get(f1, [])
        avail = [q for q in qs if _get_qid(q, f1) not in used_set]
        pool = avail if len(avail) >= 12 else (avail + [q for q in qs if q not in avail])
        return [(team, q) for q in pool[:6]] + [(opp, q) for q in pool[6:12]]
    def get_six(f):
        qs = r2.get(f, [])
        avail = [q for q in qs if _get_qid(q, f) not in used_set]
        pool = avail if len(avail) >= 6 else (avail + [q for q in qs if q not in avail])
        return pool[:6]
    return [(team, q) for q in get_six(f1)] + [(opp, q) for q in get_six(f2)]

def build_r3_queue(q_data: Dict[str, Any], team: str, opp: str, used: Set[str] = None, rep_pct: int = 0) -> List[Tuple[str, Dict[str, Any]]]:
    used_set, r3 = (used or set()) if rep_pct < 100 else set(), q_data.get("round_3", [])
    avail = [q for q in r3 if _get_qid(q, "سرعة") not in used_set]
    pool = avail if len(avail) >= 12 else (avail + [q for q in r3 if q not in avail])
    return [(team, q) for q in pool[:6]] + [(opp, q) for q in pool[6:12]]

def advance_match_phase(state: Any) -> None:
    st, opp = state.starting_team, (state.team_b if state.starting_team == state.team_a else state.team_a)
    if state.phase == "round_1":
        state.phase, state.queue, state.q_idx = "round_2_selection", [], 0
        state.current_question = {"question": "انتهت أسئلة الفقرة الأولى. يرجى اختيار مجالات الفقرة الثانية.", "field": "اختر مجالك", "correct_answer": ""}
    elif state.phase == "round_2":
        state.phase, state.q_idx = "round_3", 0
        state.queue = build_r3_queue(state.q_data, st, opp, getattr(state, "used_ids", None), getattr(state, "rep_pct", 0))
        state.load_current_from_queue()
    elif state.phase in ("round_3", "tie_breaker"):
        if state.scores[state.team_a] == state.scores[state.team_b]:
            state.phase = "tie_breaker"
            pool = state.q_data.get("starter_speed", []) + state.q_data.get("round_3", [])
            state.starter_idx = (state.starter_idx + 1) % len(pool) if pool else 0
            state.current_question = pool[state.starter_idx] if pool else None
            qid = state._qid(state.current_question)
            if qid and qid not in state.asked_q_ids: state.asked_q_ids.append(qid)
        else:
            state.phase = "finished"
            win = state.team_a if state.scores[state.team_a] > state.scores[state.team_b] else state.team_b
            state.current_question = {"question": f"انتهت المباراة بفوز فريق {win}! مبارك للفائز.", "field": "النهائي", "correct_answer": ""}
            finalize_match_record(state)

def finalize_match_record(state: Any) -> None:
    try: from .bank_storage import load_bank, save_bank, mark_questions_used, save_match_history, clear_active_match; from .match_reporter import generate_html_report; from .tournament_manager import get_active_tournament
    except (ImportError, Exception):
        try: from bank_storage import load_bank, save_bank, mark_questions_used, save_match_history, clear_active_match; from match_reporter import generate_html_report; from tournament_manager import get_active_tournament
        except Exception: get_active_tournament = lambda: "عام"
    sa, sb = state.scores.get(state.team_a, 0), state.scores.get(state.team_b, 0)
    win = state.team_a if sa > sb else (state.team_b if sb > sa else "تعادل")
    tour = getattr(state, "tournament", "") or get_active_tournament()
    m_data = {
        "match_id": state.match_id, "tournament": tour, "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "team_a": state.team_a, "team_b": state.team_b, "score_a": sa, "score_b": sb,
        "winner": win, "scores": dict(state.scores), "total_questions": len(getattr(state, "history", [])),
        "rebounds": getattr(state, "rebounds", 0), "lifelines": 8 - sum(state.lifelines.values()),
        "rounds": [
            {"name": "الفقرة الأولى", "score_a": state.r_scores.get("round_1", {}).get(state.team_a, 0), "score_b": state.r_scores.get("round_1", {}).get(state.team_b, 0), "questions": 24, "rebounds": state.r_rebounds.get("round_1", 0), "lifelines": 8 - sum(state.lifelines.values())},
            {"name": "الفقرة الثانية", "score_a": state.r_scores.get("round_2", {}).get(state.team_a, 0), "score_b": state.r_scores.get("round_2", {}).get(state.team_b, 0), "questions": 12, "rebounds": state.r_rebounds.get("round_2", 0), "lifelines": 0},
            {"name": "الفقرة الثالثة", "score_a": state.r_scores.get("round_3", {}).get(state.team_a, 0), "score_b": state.r_scores.get("round_3", {}).get(state.team_b, 0), "questions": 12, "rebounds": state.r_rebounds.get("round_3", 0), "lifelines": 0},
        ]
    }
    state.html_report = generate_html_report(m_data)
    save_match_history(m_data)
    bank = load_bank()
    mark_questions_used(bank, getattr(state, "asked_q_ids", []), state.match_id)
    save_bank(bank)
    clear_active_match()
