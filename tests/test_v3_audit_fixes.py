# -*- coding: UTF-8 -*-
"""اختبارات التحقق من الإصلاحات السبعة لمراجعة ما قبل الإطلاق (v3.0.0)."""
import os
import sys
import tempfile
import unittest
from unittest import mock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import action_dispatcher
import match_state
import question_parser
import question_replacer
import state_restorer


class TestV3AuditFixes(unittest.TestCase):
    """يتحقق من مطابقة الكود لكافة قواعد المسابقة ومنع التكرار واستعادة الإحصاءات."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._env = mock.patch.dict(os.environ, {"APPDATA": self._tmp.name})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def test_parser_strips_trailing_and_inline_asterisk_from_choices(self):
        raw = "الفقرة الأولى\nمجال: علوم\nسؤال: ما رمز الماء؟\nأ) O2\nب) H2O *\nج) CO2\nد) NaCl\n"
        parsed = question_parser.parse_questions_content(raw)
        q = parsed["round_1"]["علوم"][0]
        self.assertEqual(q["correct_index"], 1)
        self.assertEqual(q["choices"][1], "H2O")
        self.assertNotIn("*", q["choices"][1])

    def test_replacer_excludes_previously_used_ids(self):
        q_data = {
            "starter_speed": [],
            "round_1": {
                "علوم": [
                    {"id": "q1", "question": "س1؟", "field": "علوم", "choices": ["1", "2", "3", "4"], "correct_index": 0, "correct_answer": "1"},
                    {"id": "q2", "question": "س2؟", "field": "علوم", "choices": ["1", "2", "3", "4"], "correct_index": 0, "correct_answer": "1"},
                    {"id": "q_old", "question": "س قديم؟", "field": "علوم", "choices": ["1", "2", "3", "4"], "correct_index": 0, "correct_answer": "1"},
                    {"id": "q_fresh", "question": "س جديد؟", "field": "علوم", "choices": ["1", "2", "3", "4"], "correct_index": 0, "correct_answer": "1"},
                ]
            },
            "round_2": {},
            "round_3": [],
        }
        st = match_state.MatchState("أ", "ب", q_data=q_data, used_ids={"q_old"}, rep_pct=0)
        ok = question_replacer.find_and_swap_question(st)
        self.assertTrue(ok)
        self.assertEqual(st.current_question["id"], "q_fresh")

    def test_r2_field_counts_exclude_used_questions(self):
        r2_qs = [{"id": f"r2_{i}", "question": f"سؤال {i}؟", "field": "تاريخ", "correct_answer": "ج"} for i in range(14)]
        used = {f"r2_{i}" for i in range(6)}  # only 8 unused remain (< 12)
        q_data = {"starter_speed": [], "round_1": {}, "round_2": {"تاريخ": r2_qs}, "round_3": []}
        st = match_state.MatchState("أ", "ب", q_data=q_data, used_ids=used, rep_pct=0)
        self.assertEqual(st.to_dict()["r2_field_counts"]["تاريخ"], 8)
        import pool_validator
        _, _, warns = pool_validator.validate_match_pool(q_data, used_ids=used, rep_pct=0)
        self.assertTrue(any("تكرار المجال" in w and "تاريخ" in w for w in warns))

    def test_penalty_deducts_point_without_changing_question(self):
        q_data = {
            "starter_speed": [],
            "round_1": {"علوم": [
                {"id": "q1", "question": "س1؟", "field": "علوم", "choices": ["1", "2", "3", "4"], "correct_index": 0, "correct_answer": "1"},
                {"id": "q2", "question": "س2؟", "field": "علوم", "choices": ["1", "2", "3", "4"], "correct_index": 0, "correct_answer": "1"},
            ]},
            "round_2": {},
            "round_3": [],
        }
        st = match_state.MatchState("أ", "ب", q_data=q_data)
        st.scores["أ"] = 3
        s_dict = st.to_dict()
        q_before = st.current_question["id"]
        action_dispatcher.dispatch_web_action(st, "penalty", {"team": "أ"}, s_dict)
        self.assertEqual(st.scores["أ"], 2)
        self.assertEqual(st.current_question["id"], q_before)

    def test_state_restorer_preserves_round_scores_rebounds_and_asked_ids(self):
        act_m = {
            "match_id": "m1", "team_a": "أ", "team_b": "ب", "phase": "round_3",
            "scores": {"أ": 5, "ب": 4}, "lifelines": {"أ": 2, "ب": 3},
            "r_scores": {"round_1": {"أ": 3, "ب": 2}, "round_2": {"أ": 2, "ب": 2}, "round_3": {"أ": 0, "ب": 0}},
            "r_rebounds": {"round_1": 2, "round_2": 1, "round_3": 0},
            "rebounds": 3, "asked_q_ids": ["id1", "id2"],
        }
        st = state_restorer.restore_match_state(act_m, {"starter_speed": [], "round_1": {}, "round_2": {}, "round_3": []})
        self.assertEqual(st.r_scores["round_1"]["أ"], 3)
        self.assertEqual(st.r_rebounds["round_1"], 2)
        self.assertEqual(st.rebounds, 3)
        self.assertEqual(st.asked_q_ids, ["id1", "id2"])

    def test_web_ui_disables_timer_on_starter_and_rebound_and_has_penalty_buttons(self):
        with open(os.path.join(SRC_DIR, "web", "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertNotIn('id="btn-starter-timer"', html)
        self.assertIn("if (currentState.phase === 'starter_speed')", html)
        self.assertIn("if (currentState.is_rebound)", html)
        self.assertIn('id="btn-penalty-a"', html)
        self.assertIn('id="btn-penalty-b"', html)


if __name__ == "__main__":
    unittest.main()
