#!/usr/bin/env python

ver = "0.0.1"

import os
import sys
import datetime
import re
import shutil

now = datetime.datetime.now()
args = sys.argv

tim_dir = "{}/.config/tim/".format(os.path.expanduser("~"))
today_dir_path = tim_dir + "{}/{}/".format(now.year, now.month)
today = "{}{}.dat".format(today_dir_path,  now.day)

reg = re.compile('(\d\d:\d\d) *<<(.+)>> *([,a-zA-Z0-1]+)?')

# -------helpers
def touch(path):
    if not os.path.exists(path):
        with open(path, 'a'):
            os.utime(path, None)

def cat():
    path = today
    print("Tim version {}".format(ver))
    print("This day's activities ({}/{}/{})".format(now.year, now.month, now.day))
    print("-----------------------------------\n")
    f = open(path, "r")
    for l in f.readlines():
        parts = reg.match(l.strip())
        tags = ''
        if len(parts.groups()) == 3 and parts.group(3):
            tags = parts.group(3)
        print('{}  {}   [{}]'.format(parts.group(1), parts.group(2), tags))

    f.close()

def insert(text, path, minus):
    t = datetime.datetime.now() - datetime.timedelta(minutes=minus)
    msg = "{}:{} <<{}>>\n".format(t.hour, t.minute, text)
    with open(path, "a") as o:
        o.write(msg)

def load_tags():
    arr = []
    tags_path = tim_dir + "tags"
    touch(tags_path)
    with open(tags_path, "r") as f:
        arr = f.readlines()
    res = []
    for a in arr:
        res.append(a.strip())
    return res

def add_tag(tag):
    tags_path = tim_dir + "tags"
    touch(tags_path)
    with open(tags_path, "a") as o:
        o.write(tag.stri())
        o.write("\n")


def finish():
    touch(today)
    shutil.copyfile(today, today + "_back")
    lines = []
    with open(today, "r") as o:
        for l in o.readlines():
            lines.append(l.strip())
    print(lines)
    f = open(today, "w")
    for l in lines:
        parts = reg.match(l.strip())
        current_tags = ''
        if len(parts.groups()) == 3 and parts.group(3):
            current_tags = str(parts.group(3))
        print("\n")
        print('{}  {}   [{}]'.format(parts.group(1), parts.group(2), current_tags))
        print("Add tags (comma separated)...")
        inp = sys.stdin.readline().strip()
        tags = inp.strip().split(',') + current_tags.strip().split(',')
        ok_tags = set()
        all_tags = load_tags()
        for tag in tags:
            if tag not in all_tags:
                print("{} is not registered, skipping".format(tag))
            else:
                ok_tags.add(tag)
        f.write(parts.group(1))
        f.write(" <<" + parts.group(2) + ">> ")
        f.write(",".join(list(ok_tags)))
        f.write("\n")
        print("------------")
    f.close()
    cat()
    
#-----------------        

if not os.path.exists(today_dir_path):
    os.makedirs(today_dir_path)

touch(today)


if len(args) == 1:
    cat()
else:
    if args[1] == "-c":
        command = args[2]
        if command == 'tags':
            arr = load_tags()
            print(", ".join(arr))
        elif command == "add":
            add_tag(args[3])
            arr = load_tags()
            print(", ".join(arr))
        elif command == "end":
            finish()
    elif args[1] == "-t":
        diff = int(args[2])
        text = " ".join(args[3:])
        insert(text, today, diff)

    else:
        text = " ".join(args[1:])
        insert(text, today, 0)

    

