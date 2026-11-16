"""موديول استبدال وسحب الأسئلة الاحتياطية أثناء المباراة."""
from typing import Any


def find_and_swap_question(state: Any) -> bool:
    """استبدال السؤال الحالي بسؤال احتياطي جديد من نفس المجال دون التأثير على النقاط."""
    if not getattr(state, "current_question", None):
        return False
    field = state.current_question.get("field", "")
    asked = getattr(state, "asked_q_ids", [])
    backup = None

    if state.phase == "round_1":
        for q in state.q_data.get("round_1", {}).get(field, []):
            qid = q.get("id") or str(q.get("question"))
            if qid not in asked:
                backup = q
                break
    elif state.phase == "round_2":
        f = state.r2_fields.get(state.active_team, field)
        for q in state.q_data.get("round_2", {}).get(f, []):
            qid = q.get("id") or str(q.get("question"))
            if qid not in asked:
                backup = q
                break
    elif state.phase in ("round_3", "starter_speed", "tie_breaker"):
        pool_key = "round_3" if state.phase == "round_3" else "starter_speed"
        for q in state.q_data.get(pool_key, []):
            qid = q.get("id") or str(q.get("question"))
            if qid not in asked:
                backup = q
                break

    if backup:
        state.current_question = backup
        qid = backup.get("id") or str(backup.get("question"))
        asked.append(qid)
        state.is_rebound, state.options_revealed = False, False
        return True
    return False
