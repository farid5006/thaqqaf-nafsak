import os, sys, unittest, tempfile, shutil
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import bank_storage, tournament_manager, tournament_ops

class TestTournamentsV2(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch.object(bank_storage, "get_data_dir", return_value=self.test_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_legacy_matches_grouping(self):
        legacy = [
            {"match_id": "m1", "team_a": "الأحباء", "team_b": "الأبطال", "date": "2026-11-15 18:00", "tournament": ""},
            {"match_id": "m2", "team_a": "النور", "team_b": "الفرسان", "date": "2026-11-16 19:00", "tournament": "البطولة الأولى"}
        ]
        bank_storage.save_json_file(legacy, os.path.join(self.test_dir, "matches_history.json"))
        
        act = tournament_manager.get_active_tournament()
        self.assertTrue(act.startswith("بطولة 1"))
        self.assertIn("2026-11-15", act)

        matches = bank_storage.load_matches_history()
        self.assertEqual(matches[0]["tournament"], act)
        self.assertEqual(matches[1]["tournament"], act)

    def test_start_new_tournament(self):
        t1 = tournament_manager.start_new_tournament("دوري المعرفة 2026")
        self.assertEqual(tournament_manager.get_active_tournament(), "دوري المعرفة 2026")
        tours = tournament_manager.list_tournaments()
        self.assertIn("دوري المعرفة 2026", tours)

    def test_assign_and_delete_tournament(self):
        m = [
            {"match_id": "m100", "team_a": "أ", "team_b": "ب", "tournament": "بطولة رمضان"},
            {"match_id": "m200", "team_a": "ج", "team_b": "د", "tournament": "بطولة رمضان"}
        ]
        bank_storage.save_json_file(m, os.path.join(self.test_dir, "matches_history.json"))
        bank_storage.save_bank({"used": {"q1": "m100", "q2": "m200", "q3": "other_m"}})

        tournament_manager.start_new_tournament("بطولة رمضان")
        tournament_manager.start_new_tournament("بطولة العيد")

        in_ramadan = tournament_ops.get_matches_for_tournament("بطولة رمضان")
        self.assertEqual(len(in_ramadan), 2)

        # نقل مباراة
        ok = tournament_ops.assign_match_to_tournament("m100", "بطولة العيد")
        self.assertTrue(ok)
        self.assertEqual(len(tournament_ops.get_matches_for_tournament("بطولة العيد")), 1)
        self.assertEqual(len(tournament_ops.get_matches_for_tournament("بطولة رمضان")), 1)

        # حذف بطولة رمضان مع reset_questions=False (الافتراضي: لا يفرغ الأسئلة)
        del_ok = tournament_ops.delete_tournament("بطولة رمضان", reset_questions=False)
        self.assertTrue(del_ok)
        self.assertNotIn("بطولة رمضان", tournament_manager.list_tournaments())

        remaining_matches = bank_storage.load_matches_history()
        self.assertEqual(len(remaining_matches), 1)
        self.assertEqual(remaining_matches[0]["match_id"], "m100")

        # التأكد من بقاء q2 في used لأن reset_questions=False
        bank = bank_storage.load_bank()
        self.assertIn("q2", bank["used"])

        # اختبار حذف مباراة فردية مع reset_questions=True
        del_m_ok = tournament_ops.delete_match("m100", reset_questions=True)
        self.assertTrue(del_m_ok)
        self.assertEqual(len(bank_storage.load_matches_history()), 0)
        bank_after = bank_storage.load_bank()
        self.assertNotIn("q1", bank_after["used"])
        self.assertIn("q3", bank_after["used"])

if __name__ == "__main__":
    unittest.main()
