#!/usr/bin/env python3.7

from __future__ import annotations
import os
import sys
import datetime
import shutil
import readline
import json
from subprocess import call

# ------ Configurations
tim_dir = "{}/.config/tim/".format(os.path.expanduser("~"))
ver = "0.1.0"
EDITOR = os.environ.get('EDITOR', 'vim')


# ----


def create_path(year, month, day) -> str:
    return tim_dir + '{}/{}/{}.dat'.format(year, month, day)


now: datetime = datetime.datetime.now()
args = sys.argv
today_path = create_path(now.year, now.month, now.day)


class Sample(object):
    """Base sample data class, a sample contains either a message (normal event with/out a tag) or a special command,
    like end """

    def __init__(self, time: str, message: str = None, tag: str = None, command: str = None):
        self.time = time
        self.message = message
        self.tag = tag
        self.command = command
        if message is None and command is None:
            raise RuntimeError("message and command cannot be empty at the same time")
        if message is not None and command is not None:
            raise RuntimeError("Message and command cannot be non-empty at the same time")

    def hour(self) -> int:
        return int(self.time.split(':')[0])

    def minute(self) -> int:
        return int(self.time.split(':')[1])

    def to_json(self) -> json:
        return json.dumps(self.__dict__)

    def __str__(self):
        if self.command is not None:
            return '{}  {}'.format(self.time, self.command)
        else:
            return '{}  {} [{}]'.format(self.time, self.message, self.tag)

    @staticmethod
    def from_json(json_text) -> Sample:
        js_obj = json.loads(json_text)
        message = None
        tag = None
        command = None

        time = js_obj['time']
        if 'tag' in js_obj:
            tag = js_obj['tag']
        if 'command' in js_obj:
            command = js_obj['command']
        if 'message' in js_obj:
            message = js_obj['message']
        return Sample(time, message, tag, command)


def create_list_completer(ll):
    """
    This is a closure that creates a method that autocompletes from
    the given list.

    Since the autocomplete function can't be given a list to complete from
    a closure is used to create the listCompleter function with a list to complete
    from.
    """

    def list_completer(text, state):
        line = readline.get_line_buffer()

        if not line:
            return [c + " " for c in ll][state]
        else:
            return [c + " " for c in ll if c.startswith(line)][state]

    return list_completer


# -------helpers
def touch(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    if not os.path.exists(path):
        with open(path, 'a'):
            os.utime(path, None)


def insert(text, path, minus):
    t = datetime.datetime.now() - datetime.timedelta(minutes=minus)
    sample = Sample('{}:{}'.format(t.hour, t.minute), text)
    with open(path, "a") as o:
        o.write(sample.to_json())


def insert_command(text, path):
    t = datetime.datetime.now()
    msg = "{}:{} {}\n".format(t.hour, t.minute, text)
    with open(path, "a") as o:
        o.write(msg)


def load_tags():
    tags_path = tim_dir + "tags"
    touch(tags_path)
    res = []
    with open(tags_path, "r") as f:
        all_tags = f.readlines()
        for a in all_tags:
            res.append(a.strip())
    return res


def add_tag(tag):
    tags_path = tim_dir + "tags"
    touch(tags_path)
    with open(tags_path, "a") as o:
        o.write(tag.strip())
        o.write("\n")


def finish():
    touch(today_path)
    shutil.copyfile(today_path, today_path + "_back")
    lines = []
    with open(today_path, "r") as o:
        for l in o.readlines():
            lines.append(l.strip())
    print(lines)
    loaded_tags = load_tags()

    output = []
    for l in lines:
        parts = reg.match(l.strip())
        if parts is None:
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
        f = open(today_path, "w")
        f.write("\n".join(output) + "\n")
        f.close()


def get_tags(line, defined_tags):
    tab_completer = create_list_completer(defined_tags)
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(tab_completer)
    new_tags = set()
    ans = 'a'
    flag = False
    while ans.strip() != '':
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Available tags : " + ", ".join(defined_tags))
        print("---------")
        print(line + " " + ", ".join(new_tags))

        if flag:
            print("{} is not a valid tag".format(ans))
        ans = input().strip()
        if ans in defined_tags:
            new_tags.add(ans)
            flag = False
        else:
            flag = True
    return new_tags


def open_editor(path):
    call(EDITOR.split(" ") + [path])


def load_file(path) -> list[Sample]:
    arr = []
    with open(path, 'r') as f:
        for line in f.readlines():
            sample = Sample.from_json(line)
            arr.append(sample)
    return arr


def cat(date: datetime):
    path = create_path(date.year, date.month, date.day)
    print("use -h to show help and commands")
    print("-----------------------------------\n")
    arr = load_file(path)
    for sample in arr:
        print(sample)


# -----------------

touch(today_path)


def print_help():
    print("[MESSAGE] : start activity from this moment")
    print("-t [MINUTES] [MESSAGE] : Start activity from [MINUTES] ago")
    print("-c tags : list tags")
    print("-c add : add a tag")
    print("-c end : Add end to the file")
    print("-c open : Open today log in default system editor")
    print("-e : review and add tags to activities")
    print("-h : print this help")


def run():
    if len(args) == 1:
        cat(now)
        print("")
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
                insert_command("END", today_path)
            elif command == "open":
                open_editor(today_path)
        elif args[1] == "-e":
            finish()
        elif args[1] == "-h":
            print_help()
        elif args[1] == "-t":
            diff = int(args[2])
            message = " ".join(args[3:])
            insert(message, today_path, diff)

        else:
            message = " ".join(args[1:])
            insert(message, today_path, 0)


run()
