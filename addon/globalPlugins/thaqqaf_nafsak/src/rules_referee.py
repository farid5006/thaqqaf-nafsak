from typing import Any, Tuple, Dict

MatchState = Any


class MatchReferee:
    """حكم وقواعد مسابقة ثقف نفسك."""

    ROUND_1_LIMIT = 16
    ROUND_2_LIMIT = 12
    ROUND_3_LIMIT = 8

    @staticmethod
    def _get_teams(state: MatchState) -> Tuple[str, str]:
        teams = list(getattr(state, "scores", {}).keys())
        if len(teams) < 2:
            teams = list(getattr(state, "teams", ["team_a", "team_b"]))
        starter = getattr(state, "starting_team", teams[0])
        opponent = teams[1] if teams[0] == starter else teams[0]
        return starter, opponent

    def can_request_lifeline(self, state: MatchState) -> Tuple[bool, str]:
        rnd = getattr(state, "current_round", getattr(state, "phase", ""))
        if rnd != "round_1":
            return False, "وسائل المساعدة متاحة في الفقرة الأولى فقط."
        if getattr(state, "options_revealed", False):
            return False, "لا يمكن طلب وسيلة مساعدة بعد كشف الخيارات."
        if getattr(state, "is_rebound", False):
            return False, "لا يمكن طلب وسيلة مساعدة في سؤال مرتد."
        team = getattr(state, "active_team", getattr(state, "current_team", ""))
        pool = getattr(state, "lifelines", {})
        balance = pool.get(team, 0) if isinstance(pool, dict) else 0
        if balance <= 0:
            return False, "نفد رصيد الفريق من وسائل المساعدة."
        return True, "مسموح بطلب وسيلة المساعدة."

    def can_pass_to_opponent(self, state: MatchState) -> bool:
        return not bool(getattr(state, "is_rebound", False))

    def determine_next_turn(self, state: MatchState) -> Tuple[str, str, bool]:
        starter, opponent = self._get_teams(state)
        current_round = getattr(state, "current_round", getattr(state, "phase", "round_1"))
        idx = getattr(state, "q_idx", getattr(state, "question_index", 0))
        nxt = idx + 1

        if current_round == "round_1":
            if nxt < self.ROUND_1_LIMIT:
                return (starter if nxt % 2 == 0 else opponent), "round_1", False
            return starter, "round_2", False

        if current_round == "round_2":
            if nxt < self.ROUND_2_LIMIT:
                return (starter if nxt < 6 else opponent), "round_2", False
            return starter, "round_3", False

        if current_round == "round_3":
            if nxt < self.ROUND_3_LIMIT:
                return (starter if nxt < 4 else opponent), "round_3", False
            return "", "round_3", True

        return "", current_round, True

    def evaluate_match_result(self, state: MatchState) -> Dict[str, Any]:
        scores: Dict[str, int] = dict(getattr(state, "scores", {}))
        if len(scores) < 2:
            return {"winner": None, "scores": scores, "is_tie": True, "point_diff": 0}
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_team, top_score = ranked[0]
        second_score = ranked[1][1]
        is_tie = top_score == second_score
        return {
            "winner": None if is_tie else top_team,
            "scores": scores,
            "is_tie": is_tie,
            "point_diff": top_score - second_score,
        }
