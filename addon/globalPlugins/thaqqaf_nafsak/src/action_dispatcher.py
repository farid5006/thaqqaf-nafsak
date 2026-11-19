"""موديول معالجة وتنفيذ أوامر واجهة الويب على حالة المباراة مع حفظ الحالة النشطة."""
from typing import Any, Dict
try:
    from . import bank_storage
except ImportError:
    import bank_storage

def dispatch_web_action(state, action: str, body: Dict[str, Any], state_dict: Dict[str, Any]):
    if state.phase in ("round_2_selection", "finished") and action in ("correct", "wrong", "lifeline", "replace_question"):
        state_dict.clear(); state_dict.update(state.to_dict()); return

    if action == "set_starter":
        state.set_starting_team(body.get("team", state.team_a))
    elif action == "next_starter":
        state.next_starter_question()
    elif action == "choose_fields":
        f_st, f_opp = body.get("field_starter", ""), body.get("field_opp", "")
        counts = {f: len(qs) for f, qs in state.q_data.get("round_2", {}).items()}
        if f_st == f_opp and counts.get(f_st, 0) < 12: return
        state.start_round_2_with_fields(f_st, f_opp)
    elif action == "correct":
        team = body.get("team", state.active_team)
        state.advance_turn(team, is_correct=True)
    elif action == "wrong":
        if state.phase in ("round_1", "round_2", "round_3") and not state.is_rebound:
            state.pass_question_to_opponent()
        else:
            state.advance_turn(state.active_team, is_correct=False)
    elif action == "lifeline":
        t = body.get("team", state.active_team)
        if state.phase == "round_1" and state.lifelines.get(t, 0) > 0 and not state.is_rebound:
            state.lifelines[t] -= 1
            state.options_revealed = True
    elif action == "replace_question":
        state.replace_question()
    elif action in ("next", "skip"):
        state.advance_turn(state.active_team, is_correct=False)

    state_dict.clear()
    state_dict.update(state.to_dict())

    if state.phase == "finished":
        bank_storage.clear_active_match()
    else:
        bank_storage.save_active_match(state_dict)
