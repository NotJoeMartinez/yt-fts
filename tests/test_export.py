
import unittest
import os
from yt_fts.export import export_fts

class TestExportFts(unittest.TestCase):
    def test_export_fts(self):
        # Setup
        text = "oiwfjnoibne"
        scope = "all"
        channel_id = "1"
        video_id = None 

        result = export_fts(text, scope, channel_id, video_id)
        self.assertIsNone(result, "Expected None when no matches are found")

if __name__ == '__main__':
    unittest.main()