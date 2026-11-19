"""موديول استبدال وسحب الأسئلة الاحتياطية أثناء المباراة بأمان تام دون تكرار."""
from typing import Any

def find_and_swap_question(state: Any) -> bool:
    if not getattr(state, "current_question", None): return False
    field = state.current_question.get("field", "")
    asked = getattr(state, "asked_q_ids", [])
    prohibited = set(asked) | {(q.get("id") or str(q.get("question"))) for _, q in getattr(state, "queue", [])}
    backup = None

    if state.phase == "round_1":
        for q in state.q_data.get("round_1", {}).get(field, []):
            if (q.get("id") or str(q.get("question"))) not in prohibited:
                backup = q; break
        if not backup:
            for f, qs in state.q_data.get("round_1", {}).items():
                for q in qs:
                    if (q.get("id") or str(q.get("question"))) not in prohibited:
                        backup = q; break
                if backup: break
    elif state.phase == "round_2":
        f = state.r2_fields.get(state.active_team, field)
        for q in state.q_data.get("round_2", {}).get(f, []):
            if (q.get("id") or str(q.get("question"))) not in prohibited:
                backup = q; break
    elif state.phase in ("round_3", "starter_speed", "tie_breaker"):
        p = (state.q_data.get("starter_speed", []) + state.q_data.get("round_3", [])) if state.phase == "tie_breaker" else state.q_data.get("round_3" if state.phase == "round_3" else "starter_speed", [])
        for q in p:
            if (q.get("id") or str(q.get("question"))) not in prohibited:
                backup = q; break

    if backup:
        state.current_question = backup
        qid = backup.get("id") or str(backup.get("question"))
        asked.append(qid)
        state.is_rebound, state.options_revealed = False, False
        if state.queue and state.q_idx < len(state.queue):
            state.queue[state.q_idx] = (state.active_team, backup)
        return True
    return False
