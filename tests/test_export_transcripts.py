import unittest
import datetime
import os
from yt_fts.export import export_transcripts

class TestExportTranscripts(unittest.TestCase):
    def test_export_transcripts(self):
        # Setup
        channel_id = 2

        # Call the function with the test parameters
        export_transcripts(channel_id)

        # Construct the expected file name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        expected_file_name = f"channel_{channel_id}_{timestamp}.csv"

        # Check that the file was created
        self.assertTrue(os.path.exists(expected_file_name))

        # Add assertions here to check the contents of the file
        # For example, you might open the file and check that it contains the expected transcripts

if __name__ == '__main__':
    unittest.main()