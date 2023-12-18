import unittest
from unittest.mock import patch
from yt_fts.utils import split_subtitles

class TestSplitSubtitles(unittest.TestCase):
    def test_split_subtitles(self):
        # Setup
        video_id = "5XyayUs6J1M"
        # Call the function with the test parameters
        split_subtitles(video_id)

        # Add assertions here to check the behavior of the function
        # For example, you might check the output of the print statements

if __name__ == '__main__':
    unittest.main()