
import unittest
import os
from yt_fts.export import export_fts

class TestExportFts(unittest.TestCase):
    def test_export_fts(self):
        # Setup
        text = "test"
        scope = "all"
        channel_id = "1"
        video_id = None 

        export_fts(text, scope, channel_id, video_id)

        # # Check that the file was created
        # self.assertTrue(os.path.exists(expected_file_name))

        # with open(expected_file_name, 'r') as csvfile:
        #     reader = csv.reader(csvfile)
        #     # Add assertions here to check the contents of the file
        #     # For example, you might check the number of rows or the contents of the first row


        # Add assertions here to verify the function's behavior
        # For example, you might check that a file was created with the expected name and contents

if __name__ == '__main__':
    unittest.main()