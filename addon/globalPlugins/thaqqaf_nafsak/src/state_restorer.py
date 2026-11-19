"""موديول استعادة وبناء حالة المباراة المحفوظة بدقة لمواصلة اللعب."""
from typing import Any, Dict

def restore_match_state(act_m: Dict[str, Any], q_data: Dict[str, Any]):
    try: from .match_state import MatchState; from .queue_builder import build_r1_queue, build_r2_queue, build_r3_queue
    except ImportError: from match_state import MatchState; from queue_builder import build_r1_queue, build_r2_queue, build_r3_queue

    t1, t2 = act_m.get("team_a", "الفريق الأول"), act_m.get("team_b", "الفريق الثاني")
    st = MatchState(t1, t2, q_data=q_data, match_id=act_m.get("match_id"), tournament=act_m.get("tournament", ""), rep_pct=act_m.get("rep_pct", 0))
    st.phase = act_m.get("phase", "round_1")
    st.scores = dict(act_m.get("scores", st.scores))
    st.lifelines = dict(act_m.get("lifelines", st.lifelines))
    st.starting_team = act_m.get("starting_team", st.team_a)
    st.r2_fields = dict(act_m.get("r2_fields", st.r2_fields))
    st.q_idx = act_m.get("q_idx", 0)
    opp = st.team_b if st.starting_team == st.team_a else st.team_a

    if st.phase == "round_1":
        st.queue = build_r1_queue(st.q_data, st.starting_team, opp, st.used_ids, st.rep_pct)
    elif st.phase == "round_2":
        f1, f2 = st.r2_fields.get(st.starting_team, ""), st.r2_fields.get(opp, "")
        st.queue = build_r2_queue(st.q_data, st.starting_team, opp, f1, f2, st.used_ids, st.rep_pct)
    elif st.phase == "round_3":
        st.queue = build_r3_queue(st.q_data, st.starting_team, opp, st.used_ids, st.rep_pct)

    st.load_current_from_queue()
    st.active_team = act_m.get("active_team", st.active_team)
    st.is_rebound = act_m.get("is_rebound", False)
    st.options_revealed = act_m.get("options_revealed", False)
    if act_m.get("current_question"): st.current_question = act_m["current_question"]
    return st
