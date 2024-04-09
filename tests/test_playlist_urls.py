import unittest
from pprint import pprint
from unittest.mock import patch, call
import subprocess
from yt_fts.download import get_playlist_urls


class TestGetPlaylistUrls(unittest.TestCase):
    def test_bob_ross(self):
        # bobross 
        playlist_url = "https://www.youtube.com/playlist?list=PLAEQD0ULngi69x_7JbQvSMprLRK_KSVLu"

        # expected_output = ['oh5p5f5_-7A', 'RInDWhYceLU', 'UOziR7PoVco', '0pwoixRikn4', 
        #                    'DFSIQNjKRfk', 'loAzRUzx1wI', 'sDdpc8uisD0', 'kQlFwTOkYzg', 
        #                    'QxcS7p1VHyQ', 'wDnLlywAL5I', 'Q03YvknOVe0', '4E35-8x_y04', 
        #                    'IEQWfszfRlA']

        actual_output = get_playlist_urls(playlist_url)
        print(actual_output)
        # self.assertEqual(actual_output, expected_output)
        self.assertEqual(len(actual_output), 13)


if __name__ == '__main__':
    unittest.main()
