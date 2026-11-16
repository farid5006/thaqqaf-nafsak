"""اختبارات الوحدة للمرحلة الثانية: حالة المباراة، التحكيم، والتقارير."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from match_state import MatchState
from rules_referee import MatchReferee
from match_reporter import generate_text_report, generate_html_report


class TestStage2(unittest.TestCase):
    def test_match_state_and_lifelines(self):
        state = MatchState(team_a="النور", team_b="الأمل")
        state.set_starting_team("النور")
        self.assertEqual(state.scores["النور"], 0)
        self.assertEqual(state.lifelines["النور"], 3)
        self.assertEqual(state.get_timer_duration(), 45)

        # خصم مساعدة
        success = state.consume_lifeline("النور")
        self.assertTrue(success)
        self.assertEqual(state.lifelines["النور"], 2)

        # تحويل السؤال
        state.pass_question_to_opponent()
        self.assertEqual(state.active_team, "الأمل")
        self.assertTrue(state.is_rebound)

        # تسجيل إجابة صحيحة
        state.advance_turn(answered_by="الأمل", is_correct=True)
        self.assertEqual(state.scores["الأمل"], 1)

    def test_referee_rules(self):
        referee = MatchReferee()
        state = MatchState(team_a="النور", team_b="الأمل")
        state.set_starting_team("النور")

        # مسموح بطلب مساعدة
        can_help, msg = referee.can_request_lifeline(state)
        self.assertTrue(can_help)

        # إذا كُشفت الخيارات يمنع
        state.options_revealed = True
        can_help2, msg2 = referee.can_request_lifeline(state)
        self.assertFalse(can_help2)

        # تقييم النتيجة
        state.award_point("النور", 5)
        state.award_point("الأمل", 3)
        result = referee.evaluate_match_result(state)
        self.assertEqual(result["winner"], "النور")
        self.assertFalse(result["is_tie"])
        self.assertEqual(result["point_diff"], 2)

    def test_reporting(self):
        match_data = {
            "team_a": "النور",
            "team_b": "الأمل",
            "score_a": 10,
            "score_b": 8,
            "total_questions": 24,
            "rebounds": 3,
            "lifelines": 4,
            "rounds": [
                {"name": "الفقرة الأولى", "score_a": 4, "score_b": 3, "questions": 16, "rebounds": 2, "lifelines": 4},
                {"name": "الفقرة الثانية", "score_a": 4, "score_b": 3, "questions": 12, "rebounds": 1, "lifelines": 0},
                {"name": "الفقرة الثالثة", "score_a": 2, "score_b": 2, "questions": 8, "rebounds": 0, "lifelines": 0},
            ]
        }
        text_rep = generate_text_report(match_data)
        self.assertIn("الفائز: النور", text_rep)
        self.assertIn("التحويلات المرتدة: 3", text_rep)

        html_rep = generate_html_report(match_data)
        self.assertIn("<table", html_rep)
        self.assertIn("dir='rtl'", html_rep)


if __name__ == "__main__":
    unittest.main()
