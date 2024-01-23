import unittest
import os
import shutil

from pprint import pprint
from yt_fts.utils import parse_vtt

class TestParseVtt(unittest.TestCase):
    def test_parse_vtt(self):
        vtt_path = "tests/test_data/vtt/dqGyCTbzYmc.vtt"
        result = parse_vtt(vtt_path)

        pprint(result)


if __name__ == '__main__':
    unittest.main()