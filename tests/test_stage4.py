"""اختبارات الوحدة للمرحلة الرابعة: الخادم، مسارات الويب، والتكامل."""
import json
import os
import sys
import unittest
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins", "thaqqaf_nafsak")))

from server import MatchServer
from recording_bridge import RecordingBridge
from __init__ import GlobalPlugin


class TestStage4(unittest.TestCase):
    def test_server_and_api(self):
        test_state = {"team_a": "النور", "team_b": "الأمل", "score": 0}
        srv = MatchServer(state=test_state, port=8890)
        url = srv.start()
        self.assertTrue(url.startswith("http://127.0.0.1:"))

        try:
            # اختبار GET /api/state
            req = urllib.request.Request(f"{url}/api/state")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["team_a"], "النور")

            # اختبار POST /api/action
            post_req = urllib.request.Request(
                f"{url}/api/action",
                data=json.dumps({"action": "test_action"}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(post_req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
        finally:
            srv.stop()

    def test_recording_bridge_methods(self):
        bridge = RecordingBridge()
        self.assertFalse(bridge.is_recording)
        started = bridge.trigger_recording_start()
        self.assertTrue(started)
        self.assertTrue(bridge.is_recording)

        stopped = bridge.trigger_recording_stop()
        self.assertTrue(stopped)
        self.assertFalse(bridge.is_recording)

    def test_plugin_init_safe(self):
        plugin = GlobalPlugin()
        self.assertIsNotNone(plugin)
        plugin.terminate()


if __name__ == "__main__":
    unittest.main()
