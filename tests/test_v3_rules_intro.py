# -*- coding: UTF-8 -*-
"""اختبارات مرحلة القواعد الصوتية التمهيدية والبث التدريجي (HTTP Range) في v3.0.0."""
import os
import sys
import tempfile
import unittest
from unittest import mock
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import action_dispatcher
import match_state
import server


class TestV3RulesIntro(unittest.TestCase):
    """يتحقق من دورة مرحلة القواعد الصوتية والبث التدريجي دون التأثير على الأداء."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._env = mock.patch.dict(os.environ, {"APPDATA": self._tmp.name})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def _sample_qdata(self):
        return {
            "starter_speed": [{"id": "s1", "question": "سؤال سرعة 1؟", "correct_answer": "ج1"}],
            "round_1": {"علوم": [{"id": "r1", "question": "س1؟", "choices": ["أ", "ب", "ج", "د"], "correct_index": 0, "correct_answer": "أ"}]},
            "round_2": {},
            "round_3": [],
        }

    def test_play_rules_phase_and_auto_transition(self):
        st = match_state.MatchState("الأهلي", "الزمالك", q_data=self._sample_qdata(), play_rules=True)
        self.assertEqual(st.phase, "rules_intro")
        s_dict = st.to_dict()
        # Scoring must be blocked while rules audio is playing
        action_dispatcher.dispatch_web_action(st, "correct", {"team": "الأهلي"}, s_dict)
        self.assertEqual(st.scores["الأهلي"], 0)
        self.assertEqual(st.phase, "rules_intro")
        # Finishing rules must jump directly to starter_speed with the first speed question
        action_dispatcher.dispatch_web_action(st, "finish_rules", {}, s_dict)
        self.assertEqual(st.phase, "starter_speed")
        self.assertEqual(st.current_question["question"], "سؤال سرعة 1؟")

    def test_skip_rules_when_unchecked(self):
        st = match_state.MatchState("أ", "ب", q_data=self._sample_qdata(), play_rules=False)
        self.assertEqual(st.phase, "starter_speed")

    def test_rules_audio_streamed_with_http_range_and_not_cached(self):
        srv = server.MatchServer(state={"phase": "rules_intro"}, port=8790)
        url = srv.start()
        try:
            req = urllib.request.Request(f"{url}/audio/rules_intro.mp3", headers={"Range": "bytes=0-1023"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 206)
                self.assertEqual(resp.headers.get("Accept-Ranges"), "bytes")
                chunk = resp.read()
                self.assertEqual(len(chunk), 1024)
            # Large audio file must NOT be cached in RAM
            self.assertFalse(any(k.endswith("rules_intro.mp3") for k in srv._cache))
        finally:
            srv.stop()

    def test_rules_controls_present_in_web_ui(self):
        with open(os.path.join(SRC_DIR, "web", "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="rules-controls"', html)
        self.assertIn('id="audio-rules" preload="none" src="/audio/rules_intro.mp3"', html)
        self.assertIn('el.onended = () => finishRulesIntro()', html)


if __name__ == "__main__":
    unittest.main()
