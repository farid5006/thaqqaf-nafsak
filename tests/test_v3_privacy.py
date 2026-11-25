# -*- coding: UTF-8 -*-
"""اختبارات التحقق من درع خصوصية البث وبنية الإصدار الثالث (v3.0.0)."""
import os
import re
import unittest
import zipfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "src", "web", "index.html")
MANIFEST_PATH = os.path.join(BASE_DIR, "addon", "manifest.ini")
SERVER_PATH = os.path.join(BASE_DIR, "src", "server.py")
ADDON_ZIP_PATH = os.path.join(BASE_DIR, "dist", "thaqqaf_nafsak-3.0.0.nvda-addon")


class TestV3PrivacyAndRelease(unittest.TestCase):
    """يتحقق من تكامل وضع الخصوصية البصرية والحفاظ على الاختصارات في v3.0.0."""

    @classmethod
    def setUpClass(cls):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            cls.html = f.read()
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            cls.manifest = f.read()

    def test_privacy_mode_enabled_by_default(self):
        self.assertIn('<body class="privacy-mode">', self.html)
        self.assertIn('id="btn-privacy-toggle"', self.html)
        self.assertIn('aria-pressed="true"', self.html)

    def test_answer_shield_preserves_accessibility_tree(self):
        self.assertIn('id="correct-answer-text" class="answer-text" tabindex="-1"', self.html)
        self.assertIn('id="answer-privacy-shield" class="privacy-shield-overlay" aria-hidden="true"', self.html)
        self.assertIn('id="timer-box" class="timer-display" aria-hidden="true"', self.html)
        self.assertNotRegex(self.html, r'body\.privacy-mode\s+\.answer-text\s*\{[^}]*display:\s*none')
        self.assertNotRegex(self.html, r'body\.privacy-mode\s+\.answer-text\s*\{[^}]*visibility:\s*hidden')

    def test_visual_masking_and_green_option_neutralized(self):
        self.assertIn('body.privacy-mode .answer-text {', self.html)
        self.assertIn('color: transparent !important;', self.html)
        self.assertIn('filter: blur(18px);', self.html)
        self.assertIn('body.privacy-mode .option-correct {', self.html)

    def test_announce_answer_moves_focus_for_arrow_navigation(self):
        m = re.search(r'function announceAnswer\(\)\s*\{(.*?)\n    \}', self.html, re.DOTALL)
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertIn("getElementById('correct-answer-text')", body)
        self.assertIn('.focus()', body)
        self.assertIn('announce(', body)

    def test_existing_shortcuts_intact(self):
        for fn in ('announceMeta', 'focusQuestion', 'announceAnswer', 'toggleTimer', 'handleChoicesShortcut'):
            self.assertIn(f'{fn}(', self.html)

    def test_manifest_version_is_3_0_0(self):
        self.assertIn('version = 3.0.0', self.manifest)

    def test_server_uses_threaded_http_and_ignores_favicon(self):
        with open(SERVER_PATH, "r", encoding="utf-8") as f:
            srv_src = f.read()
        self.assertIn("ThreadingHTTPServer", srv_src)
        self.assertIn("/favicon.ico", srv_src)
        self.assertIn("204", srv_src)

    def test_built_addon_has_no_pycache_or_temp_files(self):
        if os.path.exists(ADDON_ZIP_PATH):
            with zipfile.ZipFile(ADDON_ZIP_PATH, "r") as zf:
                bad = [n for n in zf.namelist() if "__pycache__" in n or n.endswith((".pyc", ".pyo", ".tmp"))]
                self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
