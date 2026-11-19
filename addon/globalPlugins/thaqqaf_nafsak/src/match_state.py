import uuid
from typing import Any, Dict, List, Optional
try: from .queue_builder import build_r1_queue, build_r2_queue, advance_match_phase; from .question_replacer import find_and_swap_question
except ImportError: from queue_builder import build_r1_queue, build_r2_queue, advance_match_phase; from question_replacer import find_and_swap_question

class MatchState:
    def __init__(self, team_a: str, team_b: str, q_data: Optional[Dict[str, Any]] = None, match_id: Optional[str] = None, used_ids=None, tournament: Optional[str] = None, rep_pct: int = 0):
        self.match_id, self.team_a, self.team_b, self.tournament = match_id or str(uuid.uuid4())[:8], team_a, team_b, (tournament or "")
        self.rep_pct, self.starting_team, self.active_team = rep_pct, team_a, team_a
        self.scores, self.lifelines = {team_a: 0, team_b: 0}, {team_a: 4, team_b: 4}
        self.q_data = q_data or {"starter_speed": [], "round_1": {}, "round_2": {}, "round_3": []}
        self.used_ids, self.phase = set(used_ids or []), ("starter_speed" if q_data and q_data.get("starter_speed") else "round_1")
        self.starter_idx, self.queue, self.q_idx, self.rebounds, self.html_report = 0, [], 0, 0, ""
        self.r2_fields, self.asked_q_ids = {team_a: "", team_b: ""}, []
        self.r_scores = {p: {team_a: 0, team_b: 0} for p in ("round_1", "round_2", "round_3")}
        self.r_rebounds = {"round_1": 0, "round_2": 0, "round_3": 0}
        self.is_rebound, self.options_revealed, self.history = False, False, []
        if self.q_data.get("starter_speed"):
            st = self.q_data["starter_speed"]; av = [q for q in st if self._qid(q) not in self.used_ids]
            self.q_data["starter_speed"] = av if (self.rep_pct == 0 or len(av) >= 5) else (av + [q for q in st if q not in av])
        self._init_first_question()

    def _qid(self, q):
        if not q: return ""
        try: from .bank_storage import compute_question_id
        except ImportError: from bank_storage import compute_question_id
        return q.get("id") or compute_question_id(q.get("question", ""), q.get("field", ""))

    def _init_first_question(self):
        starters = self.q_data.get("starter_speed", [])
        if self.phase == "starter_speed" and starters:
            self.current_question = starters[self.starter_idx]
            qid = self._qid(self.current_question)
            if qid and qid not in self.asked_q_ids: self.asked_q_ids.append(qid)
        else: self.set_starting_team(self.team_a)

    def get_timer_duration(self) -> int:
        return {"starter_speed": 15, "round_1": 45, "round_2": 30, "round_3": 15, "tie_breaker": 15}.get(self.phase, 15)

    def next_starter_question(self):
        starters = self.q_data.get("starter_speed", [])
        self.starter_idx = (self.starter_idx + 1) % len(starters) if starters else 0
        self.current_question = starters[self.starter_idx] if starters else None
        qid = self._qid(self.current_question)
        if qid and qid not in self.asked_q_ids: self.asked_q_ids.append(qid)

    def set_starting_team(self, team: str):
        opp = self.team_b if team == self.team_a else self.team_a
        self.starting_team, self.active_team, self.phase = team, team, "round_1"
        self.queue, self.q_idx = build_r1_queue(self.q_data, team, opp, self.used_ids, self.rep_pct), 0
        self.load_current_from_queue()

    def start_round_2_with_fields(self, f_starter: str, f_opp: str):
        st, opp = self.starting_team, (self.team_b if self.starting_team == self.team_a else self.team_a)
        self.r2_fields[st], self.r2_fields[opp], self.phase, self.q_idx = f_starter, f_opp, "round_2", 0
        self.queue = build_r2_queue(self.q_data, st, opp, f_starter, f_opp, self.used_ids, self.rep_pct)
        self.load_current_from_queue()

    def load_current_from_queue(self):
        if self.q_idx < len(self.queue):
            self.active_team, self.current_question = self.queue[self.q_idx]
            self.is_rebound, self.options_revealed = False, False
            qid = self._qid(self.current_question)
            if qid and qid not in self.asked_q_ids: self.asked_q_ids.append(qid)
        elif self.queue: advance_match_phase(self)

    def pass_question_to_opponent(self):
        self.active_team = self.team_b if self.active_team == self.team_a else self.team_a
        self.is_rebound, self.rebounds = True, self.rebounds + 1
        self.r_rebounds[self.phase] = self.r_rebounds.get(self.phase, 0) + 1

    def consume_lifeline(self, team: str) -> bool:
        if self.lifelines.get(team, 0) <= 0: return False
        self.lifelines[team] -= 1; return True

    def award_point(self, team: str, pts: int = 1):
        if team in self.scores: self.scores[team] += pts

    def replace_question(self) -> bool: return find_and_swap_question(self)

    def advance_turn(self, answered_by: str, is_correct: bool):
        if is_correct and answered_by in self.scores:
            self.scores[answered_by] += 1; self.r_scores.setdefault(self.phase, {})[answered_by] = self.r_scores.setdefault(self.phase, {}).get(answered_by, 0) + 1
        self.history.append({"phase": self.phase, "team": answered_by, "is_correct": is_correct})
        if self.phase == "tie_breaker":
            if is_correct: advance_match_phase(self)
            else:
                self.pass_question_to_opponent(); p = self.q_data.get("starter_speed", []) + self.q_data.get("round_3", [])
                self.starter_idx = (self.starter_idx + 1) % len(p) if p else 0; self.current_question = p[self.starter_idx] if p else None
                qid = self._qid(self.current_question)
                if qid and qid not in self.asked_q_ids: self.asked_q_ids.append(qid)
            return
        self.q_idx += 1; self.load_current_from_queue()

    def to_dict(self) -> Dict[str, Any]:
        r2 = self.q_data.get("round_2", {})
        d = {"match_id": self.match_id, "tournament": self.tournament, "rep_pct": self.rep_pct, "team_a": self.team_a, "team_b": self.team_b, "starting_team": self.starting_team, "active_team": self.active_team, "scores": dict(self.scores), "lifelines": dict(self.lifelines), "phase": self.phase, "current_round": self.phase, "current_question": self.current_question, "is_rebound": self.is_rebound, "options_revealed": self.options_revealed, "r2_available_fields": list(r2.keys()), "r2_field_counts": {f: len(qs) for f, qs in r2.items()}, "r2_fields": self.r2_fields, "q_idx": self.q_idx, "queue_len": len(self.queue), "rebounds": self.rebounds, "html_report": self.html_report}
        return d
