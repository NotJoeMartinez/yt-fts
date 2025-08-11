"""
This is where I'm putting all the functions that don't belong anywhere else
"""
import datetime
import re
import sqlite3
from typing import TypedDict
import webvtt


def show_message(code: str) -> None:
    error_dict = {
        "search_too_long": "Error: Search text must be less than 40 characters",
        "no_matches_found": "No matches found.\n- Try shortening the search text or use wildcards to match partial "
                            "words.",
        "channel_not_found": "channel not found.\n- Try using channel id",
        "multiple_channels_found": "Multiple channels found.\n- Try using id",
        "channel_url_not_correct": "The given channel URL is not correct, expected pattern : "
                                   "https://www.youtube.com/@TimDillonShow/videos",
    }

    print(error_dict[code])


def time_to_secs(time_str: str) -> int:
    """
    converts timestamp to seconds youtube urls. Subtracts 3 seconds to give a buffer. 
    """
    time_rex = re.search(r"^(\d\d):(\d\d):(\d\d)", time_str)
    hours = int(time_rex.group(1)) * 3600
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3))
    total_secs = hours + mins + secs

    return total_secs - 3


def parse_vtt(vtt_path: str) -> list[dict[str, str]]:

    result = word_level_vtt_parser(vtt_path)

    if len(result) == 0:
        result = normal_vtt_parser(vtt_path)
    
    if len(result) == 0:
        print(f"Error: Failed to parse subtitles for: {vtt_path}")

    return result


def normal_vtt_parser(vtt_path: str) -> list[dict[str, str]]:

    result = []

    for caption in webvtt.read(vtt_path):
        start_time = caption.start
        stop_time = caption.end
        text = caption.text
        result.append({
            'start_time': start_time,
            'stop_time': stop_time,
            'text': text,
        })

    return result


def word_level_vtt_parser(vtt_path: str) -> list[dict[str, str]]:
    """
    extracts start time and text from vtt file and return a list of dicts
    """
    result = []

    time_pattern = "^(.*) align:start position:0%"

    with open(vtt_path, "r") as f:
        lines = f.readlines()

    for count, line in enumerate(lines):
        time_match = re.match(time_pattern, line)

        if time_match:
            start = re.search("^(.*) -->", time_match.group(1))
            start_time = start.group(1)

            stop = re.search("--> (.*)", time_match.group(1))
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


class Model(TypedDict):
    name: str
    api_key: str
    base_url: str
    embedding_model: str
    chat_model: str

def get_model_config(api_key: str | None = None) -> Model:
    import os

    models: list[Model] = [
        {"name": "OPENAI", "embedding_model": "text-embedding-ada-002", "chat_model": "gpt-4o", "api_key": "", "base_url": "https://api.openai.com/v1"},
        {"name": "GEMINI", "embedding_model": "text-embedding-004", "chat_model": "gemini-2.5-flash", "api_key": "", "base_url": "https://generativelanguage.googleapis.com/v1beta"},
    ]

    if api_key is not None:
        # Gemini API keys start with "AIza"
        # OpenAI API keys start with "sk-"
        if api_key.startswith("sk-"):
            models[0]['api_key'] = api_key
            return models[0]
        elif api_key.startswith("AIza"):
            models[1]['api_key'] = api_key
            return models[1]
    else:
      for model in models:
          api_key = os.environ.get(f"{model['name']}_API_KEY")
          if api_key is not None:
              model['api_key'] = api_key
              return model
    
    raise ValueError("No model configuration found. Please set the environment variable for the model API key.")

def get_time_delta(timestamp1: str, timestamp2: str) -> str:
    from datetime import datetime
    format_string = "%H:%M:%S.%f"
    dt1 = datetime.strptime(timestamp1, format_string)
    dt2 = datetime.strptime(timestamp2, format_string)
    diff = dt2 - dt1
    # convert to string "HH:MM:SS"
    diff = str(diff).split(".")[0]

    return diff


def get_date(date_string: str) -> datetime.date:
    # Python 3.11 would support datimetime.date.fromisoformat('YYYYMMDD') directly
    if '-' in date_string:
        return datetime.date.fromisoformat(date_string)
    return datetime.datetime.strptime(date_string, '%Y%m%d').date()


# check if semantic search has been enabled for channel
def check_ss_enabled(channel_id: str | None = None) -> bool:
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


def enable_ss(channel_id: str) -> None:
    from yt_fts.config import get_db_path

    con = sqlite3.connect(get_db_path())
    cur = con.cursor()

    cur.execute(""" 
        INSERT INTO SemanticSearchEnabled (channel_id)
        VALUES (?)
        """, [channel_id])
    con.commit()
    con.close()


def bold_query_matches(text: str, query: str) -> str:
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


def handle_reject_consent_cookie(channel_url: str, s) -> None:
    """
    Auto rejects the consent cookie if request is redirected to the consent page
    """
    r = s.get(channel_url)
    if "https://consent.youtube.com" in r.url:
        m = re.search(r"<input type=\"hidden\" name=\"bl\" value=\"([^\"]*)\"", r.text)
        if m:
            data = {
                "gl": "DE",
                "pc": "yt",
                "continue": channel_url,
                "x": "6",
                "bl": m.group(1),
                "hl": "de",
                "set_eom": "true"
            }
            s.post("https://consent.youtube.com/save", data=data)
