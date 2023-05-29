import re

def show_message(code):
    error_dict = {
        "search_too_long": "Error: Search text must be less than 40 characters",
        "no_matches_found": "No matches found.\n- Try shortening the search text or use wildcards to match partial words."
    }

    print(error_dict[code])


def time_to_secs(time_str):
    time_rex = re.search("^(\d\d):(\d\d):(\d\d)",time_str)
    hours = int(time_rex.group(1)) * 3600 
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3)) 
    total_secs =  hours + mins + secs

    return total_secs - 3
