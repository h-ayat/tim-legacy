#!/usr/bin/env python

ver = "0.0.1"

import os
import sys
import datetime
import re
import shutil
import readline
from subprocess import call

EDITOR = os.environ.get('EDITOR','vim')

now = datetime.datetime.now()
args = sys.argv

tim_dir = "{}/.config/tim/".format(os.path.expanduser("~"))
today_dir_path = tim_dir + "{}/{}/".format(now.year, now.month)
today = "{}{}.dat".format(today_dir_path,  now.day)

reg = re.compile('(\d?\d:\d?\d) *<<(.+)>> *([,a-zA-Z0-1]+)?')

class tabCompleter(object):
    def createListCompleter(self,ll):
        """ 
        This is a closure that creates a method that autocompletes from
        the given list.
        
        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the listCompleter function with a list to complete
        from.
        """
        def listCompleter(text,state):
            line   = readline.get_line_buffer()

            if not line:
                return [c + " " for c in ll][state]
            else:
                return [c + " " for c in ll if c.startswith(line)][state]
    
        self.listCompleter = listCompleter



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
        if parts != None:
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

def insert_command(text, path):
    t = datetime.datetime.now()
    msg = "{}:{} {}\n".format(t.hour, t.minute, text)
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
        o.write(tag.strip())
        o.write("\n")


def finish():
    touch(today)
    shutil.copyfile(today, today + "_back")
    lines = []
    with open(today, "r") as o:
        for l in o.readlines():
            lines.append(l.strip())
    print(lines)
    loaded_tags = load_tags()

    output = []
    for l in lines:
        parts = reg.match(l.strip())
        if parts == None:
            output.append(l)
        else:
            current_tags = ''
            if len(parts.groups()) == 3 and parts.group(3):
                current_tags = str(parts.group(3))
            print("\n")
            text = '{}  {}   [{}]'.format(parts.group(1), parts.group(2), current_tags)
            tags = get_tags(text, loaded_tags) 
            ok_tags = set()
            all_tags = load_tags()
            for tag in tags:
                if tag not in all_tags:
                    print("{} is not registered, skipping".format(tag))
                else:
                    ok_tags.add(tag)
            current_line = parts.group(1) + " <<" + parts.group(2) + ">> " + ",".join(list(ok_tags))
            output.append(current_line)
            print("------------")

    os.system('cls' if os.name == 'nt' else 'clear')        
    print("\n".join(output))
    result = input("Save ? (Y/n)")
    if result == "y" or result == "Y" or result == "":
        f = open(today, "w")
        f.write("\n".join(output) + "\n")
        f.close()



def get_tags(line, tags):
    t = tabCompleter()
    t.createListCompleter(tags)
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(t.listCompleter)
    arr = set()
    ans = 'a'
    flag = False
    while ans.strip() != '':
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Available tags : " + ", ".join(tags))
        print("---------")
        print(line + " " + ", ".join(arr))

        if flag:
            print("{} is not a valid tag".format(ans))
        ans = input().strip()
        if ans in tags:
            arr.add(ans)
            flag = False
        else:
            flag = True
    return arr


def open(path):
     call(EDITOR.split(" ") + [path])
#-----------------        

if not os.path.exists(today_dir_path):
    os.makedirs(today_dir_path)

touch(today)


if len(args) == 1:
    cat()
    print("\nuse -h to see options and help")
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
            insert_command("END", today)
        elif command == "open":
            open(today)
    elif args[1] == "-e":
        finish()
    elif args[1] == "-h":
        print("[MESSAGE] : start activity from this moment")
        print("-t [MINUTES] [MESSAGE] : Start activity from [MINUTES] ago")
        print("-c tags : list tags")
        print("-c add : add a tag")
        print("-c end : Add end to the file")
        print("-c open : Open today log in default system editor")
        print("-e : review and add tags to activities")
        print("-h : print this help")
    elif args[1] == "-t":
        diff = int(args[2])
        text = " ".join(args[3:])
        insert(text, today, diff)

    else:
        text = " ".join(args[1:])
        insert(text, today, 0)

    

