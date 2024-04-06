"""
This is where I'm putting all the functions that don't belong anywhere else
"""
import re
import sqlite3

def show_message(code):
    error_dict = {
        "search_too_long": "Error: Search text must be less than 40 characters",
        "no_matches_found": "No matches found.\n- Try shortening the search text or use wildcards to match partial words.",
        "channel_not_found": "channel not found.\n- Try using channel id",
        "multiple_channels_found": "Multiple channels found.\n- Try using id",
        "channel_url_not_correct": "The given channel URL is not correct, expected pattern : https://www.youtube.com/@TimDillonShow/videos",
    }

    print(error_dict[code])


def time_to_secs(time_str):
    """
    converts timestamp to seconds youtube urls. Subtracts 3 seconds to give a buffer. 
    """
    time_rex = re.search("^(\d\d):(\d\d):(\d\d)",time_str)
    hours = int(time_rex.group(1)) * 3600 
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3)) 
    total_secs =  hours + mins + secs

    return total_secs - 3


def parse_vtt(file_path):
    """
    extracts start time and text from vtt file and return a list of dicts
    """
    result = []

    time_pattern = "^(.*) align:start position:0%"

    with open(file_path, "r") as f:
        lines = f.readlines()

    for count, line in enumerate(lines):
        time_match = re.match(time_pattern, line)

        if time_match:
            start = re.search("^(.*) -->",time_match.group(1))
            start_time = start.group(1)

            stop = re.search("--> (.*)",time_match.group(1))
            stop_time = stop.group(1)

            sub_titles = lines[count + 1]

            # prevent duplicate entries
            if result and result[-1]['text'] == sub_titles.strip('\n'):
                # replace the previous entry with the new one
                result[-1] = {
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'text': sub_titles.strip('\n'),
                }
            else:   
                result.append({
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'text': sub_titles.strip('\n'),
                })

    return result 


def get_api_key():
    import os
    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key is None:
        return None
    return api_key


def get_time_delta(timestamp1, timestamp2):
    from datetime import datetime
    format_string = "%H:%M:%S.%f"
    dt1 = datetime.strptime(timestamp1, format_string)
    dt2 = datetime.strptime(timestamp2, format_string)
    diff = dt2 - dt1
    # convert to string "HH:MM:SS"
    diff = str(diff).split(".")[0]

    return diff 


# check if semantic search has been enabled for channel
def check_ss_enabled(channel_id=None):

    from yt_fts.config import get_db_path

    con = sqlite3.connect(get_db_path())
    cur = con.cursor()

    if channel_id is None:
        cur.execute(""" 
            SELECT channel_id FROM SemanticSearchEnabled 
            """)
    else:
        cur.execute(""" 
            SELECT channel_id FROM SemanticSearchEnabled 
            WHERE channel_id = ?
            """, [channel_id])

    res = cur.fetchone()
    if res is None:
        return False 
    else:
        return True 


# enable semantic search for channel
def enable_ss(channel_id):
    from yt_fts.config import get_db_path

    con = sqlite3.connect(get_db_path())
    cur = con.cursor()

    cur.execute(""" 
        INSERT INTO SemanticSearchEnabled (channel_id)
        VALUES (?)
        """, [channel_id])
    con.commit()
    con.close() 


def split_subtitles(video_id):

    from datetime import datetime
    from .db_utils import get_subs_by_video_id

    def time_to_seconds(time_str):
        """ Convert time string to total seconds """
        return datetime.strptime(time_str, '%H:%M:%S.%f').time().hour * 3600 + \
            datetime.strptime(time_str, '%H:%M:%S.%f').time().minute * 60 + \
            datetime.strptime(time_str, '%H:%M:%S.%f').time().second + \
            datetime.strptime(time_str, '%H:%M:%S.%f').time().microsecond / 1e6


    subs = get_subs_by_video_id(video_id)

    if len(subs) == 0:
        print("Video is too short to split")
        return None

    total_seconds = time_to_secs(subs[-1][1])

    if (total_seconds < 10):
        print("Video is too short to split")
    


    # Convert times to seconds and store texts
    converted_data = [(time_to_seconds(start), start, text) for start, end, text in subs]

    interval_texts = {}
    for start, start_time_str, text in converted_data:
        interval = int(start // 10) * 10  
        key = interval_texts.setdefault(interval, {'start_time': start_time_str, 'texts': []})
        key['texts'].append(text)


    result = [(data['start_time'], ' '.join(data['texts']).strip()) for data in interval_texts.values()]
    return result


def bold_query_matches(text, query):
    """
    Bold the query in the text, keeping the case the same
    """
    query_words = query.lower().split()
    result_words = []

    for word in text.split():
        if word.lower() in query_words:
            result_words.append(f"[bold][bright_magenta]{word}[/bright_magenta][/bold]")
        else:
            result_words.append(word)

    return ' '.join(result_words)
