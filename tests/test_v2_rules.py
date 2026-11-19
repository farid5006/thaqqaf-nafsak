"""اختبارات القواعد الجديدة والتحصينات الأمنية للنسخة 2.0."""
import os, sys, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from match_state import MatchState
from queue_builder import build_r1_queue, build_r3_queue
from pool_validator import can_bypass_r1_deficit
from question_replacer import find_and_swap_question
from state_restorer import restore_match_state

class TestV2Rules(unittest.TestCase):
    def test_lifelines_count_is_four(self):
        st = MatchState(team_a="النور", team_b="الأمل")
        self.assertEqual(st.lifelines["النور"], 4)
        self.assertEqual(st.lifelines["الأمل"], 4)

    def test_r1_queue_exact_three_questions_per_field(self):
        # 8 مجالات في كل منها 3 أسئلة بالضبط (24 سؤالاً)
        q_data = {"round_1": {f"مجال_{i}": [{"question": f"س_{i}_{j}", "field": f"مجال_{i}"} for j in range(3)] for i in range(8)}}
        queue = build_r1_queue(q_data, "النور", "الأمل")
        self.assertEqual(len(queue), 24)
        self.assertEqual(len([q for q in queue if q[0] == "النور"]), 12)
        self.assertEqual(len([q for q in queue if q[0] == "الأمل"]), 12)

    def test_question_replacer_no_collision_with_queue(self):
        q_data = {"round_1": {"علوم": [{"question": "س1", "field": "علوم"}, {"question": "س2", "field": "علوم"}, {"question": "س3_احتياطي", "field": "علوم"}]}}
        st = MatchState("النور", "الأمل", q_data=q_data)
        st.phase = "round_1"
        st.queue = [("النور", q_data["round_1"]["علوم"][0]), ("الأمل", q_data["round_1"]["علوم"][1])]
        st.current_question = q_data["round_1"]["علوم"][0]
        st.asked_q_ids = ["س1"]
        ok = find_and_swap_question(st)
        self.assertTrue(ok)
        self.assertEqual(st.current_question["question"], "س3_احتياطي")
        self.assertNotIn("س2", st.current_question["question"])

    def test_state_restorer_preserves_rebound_and_revealed(self):
        act_m = {
            "team_a": "النور", "team_b": "الأمل", "phase": "round_1",
            "active_team": "الأمل", "is_rebound": True, "options_revealed": True, "q_idx": 1,
            "current_question": {"question": "سؤال محول", "field": "علوم"}
        }
        st = restore_match_state(act_m, {"round_1": {"علوم": [{"question": "س1"}, {"question": "س2"}]}})
        self.assertTrue(st.is_rebound)
        self.assertTrue(st.options_revealed)
        self.assertEqual(st.active_team, "الأمل")
        self.assertEqual(st.current_question["question"], "سؤال محول")

if __name__ == "__main__":
    unittest.main()
