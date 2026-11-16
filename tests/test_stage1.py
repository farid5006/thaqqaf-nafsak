"""اختبارات الوحدة للمرحلة الأولى: قراءة وتحليل وفحص بنك الأسئلة."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from file_reader import read_text_from_file
from question_parser import parse_questions_content
from pool_validator import validate_match_pool, summarize_pool
from bank_storage import (
    compute_question_id,
    load_bank,
    save_bank,
    get_unused_questions,
    mark_question_used,
)


class TestStage1(unittest.TestCase):
    def test_parser_and_validator_incomplete(self):
        sample_text = """
فقرة أسئلة السرعة لتحديد الفريق البادئ
سؤال: ما هو أسرع حيوان؟

الفقرة الأولى
[مجال: علوم]
سؤال: ما هو الكوكب الأحمر؟
أ) الأرض
*ب) المريخ
ج) الزهرة
د) عطارد

سؤال: ما هو أسرع حيوان بري؟
أ) الأسد
*ب) الفهد
ج) الغزال
د) النمر
"""
        data = parse_questions_content(sample_text)
        self.assertIn("علوم", data["round_1"])
        self.assertEqual(len(data["round_1"]["علوم"]), 2)

        # فحص الحظر والرفض الصارم عند نقص الأسئلة
        is_ready, errors, warnings = validate_match_pool(data)
        self.assertFalse(is_ready)
        self.assertTrue(len(errors) > 0)

    def test_bank_storage_atomic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            f_path = os.path.join(tmp_dir, "bank.json")
            bank = load_bank(f_path)
            self.assertEqual(bank["questions"], [])

            q_id = compute_question_id("ما هو الكوكب الأحمر؟", "علوم")
            self.assertTrue(len(q_id) > 10)

            bank["questions"].append({"id": q_id, "round_key": "round_1", "field": "علوم"})
            save_bank(bank, f_path)

            loaded = load_bank(f_path)
            self.assertEqual(len(loaded["questions"]), 1)

            unused = get_unused_questions(loaded, "round_1", "علوم")
            self.assertEqual(len(unused), 1)

            mark_question_used(loaded, q_id, "match_101")
            save_bank(loaded, f_path)

            loaded_again = load_bank(f_path)
            self.assertIn(q_id, loaded_again["used"])
            unused_after = get_unused_questions(loaded_again, "round_1", "علوم")
            self.assertEqual(len(unused_after), 0)


if __name__ == "__main__":
    unittest.main()
