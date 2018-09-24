#!/usr/bin/env python

ver = "0.0.1"

import os
import sys
import datetime

now = datetime.datetime.now()
args = sys.argv


# -------helpers
def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def cat(path):
    print("Tim version {}".format(ver))
    print("This day's activities ({}/{}/{})".format(now.year, now.month, now.day))
    print("-----------------------------------\n")
    f = open(path, "r")
    text = f.read()
    print(text)
    f.close()

def insert(text, path, minus):
    t = datetime.datetime.now() - datetime.timedelta(minutes=minus)
    msg = "{}:{} {}\n".format(t.hour, t.minute, text)
    with open(path, "a") as o:
        o.write(msg)

        
#-----------------        


today_dir_path = "{}/.config/tim/{}/{}/".format(os.path.expanduser("~"),  now.year, now.month)
today = "{}{}.txt".format(today_dir_path,  now.day)

if not os.path.exists(today_dir_path):
    os.makedirs(today_dir_path)

if not os.path.exists(today):
    touch(today)


if len(args) == 1:
    cat(today)
else:
    if args[1] == "-c":
        command = args[2]        
    elif args[1] == "-t":
        diff = int(args[2])
        text = " ".join(args[3:])
        insert(text, today, diff)

    else:
        text = " ".join(args[1:])
        insert(text, today, 0)

    

