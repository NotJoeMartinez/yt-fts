import unittest
import os
import shutil

from pprint import pprint
from yt_fts.utils import parse_vtt

class TestParseVtt(unittest.TestCase):
    def test_parse_vtt(self):

        source = "tests/test_data/vtt/test.vtt"
        dest = "tests/test.vtt"

        shutil.copy2(source, dest)
        temp_path = "tests/test.vtt"

        result = parse_vtt(temp_path)

        pprint(result)

        os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()