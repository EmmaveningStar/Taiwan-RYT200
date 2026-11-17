import unittest
from unittest.mock import patch
import update

URL = "https://script.google.com/macros/s/example/exec"

class GoogleFeedTests(unittest.TestCase):
    def test_only_explicit_approval_is_published(self):
        rows = [
            {"approved": True, "body": "核准內容", "title": "老師", "url": "https://example.com"},
            {"approved": False, "body": "未核准內容"},
            {"body": "無審核內容"},
            {"approved": "true", "body": "錯誤格式"},
        ]
        with patch.object(update, "request_json", return_value={"version": 1, "notes": rows}):
            notes = update.google_approved_notes(URL)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["body"], "核准內容")

    def test_unsafe_source_is_omitted(self):
        with patch.object(update, "request_json", return_value={
            "version": 1, "notes": [{"approved": True, "body": "心得", "url": "javascript:alert(1)"}]
        }):
            self.assertNotIn("url", update.google_approved_notes(URL)[0])

    def test_broken_feed_blocks_deployment(self):
        with patch.object(update, "request_json", return_value={}):
            with self.assertRaises(ValueError):
                update.google_approved_notes(URL)

if __name__ == "__main__":
    unittest.main()
