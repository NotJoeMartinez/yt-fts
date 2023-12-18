import unittest
from openai import OpenAI
import os
from yt_fts.vector_search import search_chroma_db

class TestSearchChromaDb(unittest.TestCase):
    def test_search_chroma_db(self):
        # Setup
        text = "nural network"
        scope = "all"
        video_id = None
        channel_id = None
        limit = 5
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        result = search_chroma_db(text, scope, channel_id, video_id, limit, client)
        self.assertEqual(len(result), 5)
    
    def test_search_chroma_db_channel(self):
        text = "nural network"
        scope = "channel"
        video_id = None
        channel_id = "1"
        limit = 5
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        result = search_chroma_db(text, scope, channel_id, video_id, limit, client)
        self.assertEqual(len(result), 5)

if __name__ == '__main__':
    unittest.main()