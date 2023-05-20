import sys, sqlite3, re

def main():

    if len(sys.argv) < 2:
        print("Need quote as argument")
        exit(0)
    else:
        get_quotes(sys.argv[1])

def get_quotes(quote):

    con = sqlite3.connect("yt_fts.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM rick WHERE sub_titles LIKE ?", ('%'+quote+'%',))
    res = cur.fetchall()
    con.close()

    if len(res) == 0:
        print("No matches found")
    else:

        shown_titles = []
        shown_stamps = []

        for quote in res: 
            vid_id = quote[0]
            vid_title = quote[1]
            start = quote[2]
            end = quote[3]
            subs = quote[4]

            #  should look like: 6C7vx4Ot2qk01:28:00
            id_stamp =  vid_id + start[:-4]  

            time = time_to_secs(start) 

            if vid_title not in shown_titles:
                print(f"\nMatches found in: \"{vid_title}\"")
                shown_titles.append(vid_title)


            if id_stamp not in shown_stamps:
                print(f"\n") 
                print(f"    Quote: \"{subs.strip()}\"")
                print(f"    Time Stamp: {start}")
                print(f"    Link: https://youtu.be/{vid_id}?t={time}")
                shown_stamps.append(id_stamp)



def time_to_secs(time_str):

    time_rex = re.search("^(\d\d):(\d\d):(\d\d)",time_str )
    hours = int(time_rex.group(1)) * 3600 
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3)) 

    total_secs =  hours + mins + secs
    return total_secs - 3




if __name__ == '__main__':
    main()