#!/usr/bin/env python3

from __future__ import annotations
import os
import sys
import shutil
import readline
import json
import re
from subprocess import call
import requests
import json
from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzlocal

tzname = datetime.now(tzlocal()).tzname()

# ------ Configurations
tim_dir = "{}/.config/tim/".format(os.path.expanduser("~"))
ver = "0.1.0"
EDITOR = os.environ.get('EDITOR', 'vim')

jira_config = {}


# ----

def clean_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def create_path(year, month, day) -> str:
    return tim_dir + '{}/{}/{}.dat'.format(year, month, day)


def date_to_path(date: datetime) -> str:
    return create_path(date.year, date.month, date.day)


now: datetime = datetime.now()
args = sys.argv
today_path = create_path(now.year, now.month, now.day)


def clean_time(time: str) -> str:
    (h, m) = time.split(':')
    h = ('0' + h) if len(h) == 1 else h
    m = ('0' + m) if len(m) == 1 else m
    return '{}:{}'.format(h, m)


class Sample(object):
    """Base sample data class, a sample contains either a message (normal event with/out a tag) or a special command,
    like end """

    def __init__(self, time: str, message: str = None, tag: str = None, command: str = None, jira_sync: bool = False,
                 jira_skip=False):
        self.time: str = clean_time(time)
        self.message: str = message
        self.tag: str = tag
        self.command: str = command
        self.jira_sync = jira_sync
        self.jira_skip = jira_skip
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
            t = '' if self.tag is None else self.tag
            return '{:>5s}  [{:^13s}]    {}'.format(self.time, t, self.message)

    @staticmethod
    def from_json(json_text) -> Sample:
        js_obj = json.loads(json_text)
        message = None
        tag = None
        command = None
        jira_sync = False
        jira_skip = False

        time = js_obj['time']
        if 'tag' in js_obj:
            tag = js_obj['tag']
        if 'command' in js_obj:
            command = js_obj['command']
        if 'message' in js_obj:
            message = js_obj['message']
        if 'jira_sync' in js_obj:
            jira_sync = js_obj['jira_sync']
        if 'jira_skip' in js_obj:
            jira_skip = js_obj['jira_skip']
        return Sample(time, message, tag, command, jira_sync, jira_skip)


def create_list_completer(ll):
    """
    This is a closure that creates a method that auto-completes from
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

def days_ago(days: int) -> datetime:
    return now - timedelta(days=days)


def touch(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    if not os.path.exists(path):
        with open(path, 'a'):
            os.utime(path, None)


def insert(text: str, path: str, minus: int, tag=None):
    t = datetime.now() - timedelta(minutes=minus)
    sample = Sample('{}:{}'.format(t.hour, t.minute), text, tag)
    insert_sample(sample, path)


def insert_sample(sample: Sample, path: str):
    with open(path, "a") as o:
        o.write(sample.to_json())
        o.write("\n")


def insert_command(command: str, path: str, time: str):
    sample = Sample(time, None, None, command)
    with open(path, "a") as o:
        o.write(sample.to_json())
        o.write("\n")


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


def validate_end_time(given: str, last: str) -> bool:
    if re.match(r'^[0-9]+:[0-9]+$', given):
        [hs, ms] = given.split(':')
        (h, m) = (int(hs), int(ms))
        if h < 24 and m < 60:
            if last is None:
                return True
            else:
                [hhs, mms] = last.split(':')
                (hh, mm) = (int(hhs), int(mms))
                return h > hh or (h == hh and m >= mm)

    return False


def get_yes_no(message: str, default_flag: bool = True) -> bool:
    complete_message = message + ('(Y/n)' if default_flag else '(y/N)')
    while True:
        result = input(complete_message).lower()
        if result == '':
            return default_flag
        elif result == 'y' or result == 'yes':
            return True
        elif result == 'n' or result == 'no':
            return False
        else:
            print('Please enter y or n (empty is treated as default value)')


def get_end_hour(last: str = None) -> str:
    message = 'Enter end hour' + ('(last Time stamp : {}) :'.format(last) if last is not None else ':')
    while True:
        result = input(message)
        if validate_end_time(result, last):
            return result


def review(date: datetime, skip_tagged: bool = True):
    clean_screen()
    print("{}/{}/{} Logs:".format(date.year, date.month, date.day))
    path = date_to_path(date)
    touch(path)
    shutil.copyfile(today_path, today_path + "_back")
    samples = load_file(path)
    loaded_tags = load_tags()
    changed = False
    for sample in samples:
        if sample.message is not None and (not (skip_tagged and sample.tag is not None)):
            prev = sample.tag
            get_tag(sample, loaded_tags)
            if prev != sample.tag:
                changed = True

    for sample in samples:
        print(sample)

    if len(samples) != 0 and samples[-1].command is None:
        if get_yes_no('This timesheet is not ended, would you like to End?'):
            end_time = get_end_hour(samples[-1].time)
            sample = Sample(end_time, None, None, 'END')
            samples.append(sample)
            changed = True

    if changed and get_yes_no('Save?'):
        print('saving')
        save_file(samples, path)


def get_tag(sample: Sample, defined_tags: [str]):
    tab_completer = create_list_completer(defined_tags)
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(tab_completer)

    flag = True
    tag = ''
    while flag:
        clean_screen()
        print("Available tags : " + ", ".join(defined_tags))
        print("---------")
        print(sample)
        if tag != '':
            print("{} is not a valid tag".format(tag))
        tag = input().strip()
        if tag in defined_tags:
            sample.tag = tag
            flag = False
        elif tag == '':
            flag = False


def open_editor(path):
    call(EDITOR.split(" ") + [path])


def save_file(samples: [Sample], path: str):
    with open(path, 'w') as f:
        f.write("\n".join(map(lambda x: x.to_json(), samples)))
        f.write("\n")


def load_file(path) -> [Sample]:
    arr = []
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f.readlines():
                if line.strip() != '':
                    sample = Sample.from_json(line.strip())
                    arr.append(sample)
    return arr


def cat(date: datetime):
    path = create_path(date.year, date.month, date.day)
    print("{}/{}/{} Logs:".format(date.year, date.month, date.day))
    print("use -h to show help and commands")
    print("-----------------------------------\n")
    arr = load_file(path)
    for sample in arr:
        print(sample)


# -----------------

touch(today_path)


def load_and_clean_all(first: int, last: int) -> [[Sample]]:
    arr = []
    for x in range(first, last + 1):
        date = days_ago(x)
        path = date_to_path(date)
        review(date, True)
        this_day = load_file(path)
        if len(this_day) > 0:
            arr.append(this_day)
    return arr


def diff(start: Sample, end: Sample) -> int:
    return diff_times(start.time, end.time)


def diff_times(start: str, end: str) -> int:
    (shs, sms) = start.split(':')
    (sh, sm) = (int(shs), int(sms))

    (ehs, ems) = end.split(':')
    (eh, em) = (int(ehs), int(ems))

    return (em - sm) + 60 * (eh - sh)


def add_dict(dic, key, value):
    if key in dic:
        dic[key] += value
    else:
        dic[key] = value


def summarize(start: int, end: int):
    data = load_and_clean_all(start, end)
    day_length = []
    tag_length = {}
    tag_count = {}
    issue_sum = {}

    for day in data:
        prev = None

        buffer = 0

        le = diff(day[0], day[-1])
        day_length.append(le)
        for sample in day:
            if prev is None:
                prev = sample
                continue

            tag = prev.tag
            d = diff(prev, sample)
            if prev.message.startswith("#"):
                add_dict(issue_sum, prev.message, d)

            if buffer != 0:
                buffer += d
                if sample.tag != tag:
                    add_dict(tag_count, tag, 1)
                    add_dict(tag_length, tag, buffer)
                    buffer = 0
            else:
                if tag == sample.tag:
                    buffer = d
                else:
                    add_dict(tag_count, tag, 1)
                    add_dict(tag_length, tag, d)
            prev = sample

    def avg(arr):
        if len(arr) == 0:
            return 0
        else:
            return sum(arr) / len(arr)

    def per(total: int, n: int) -> float:
        return int(n * 1000 / total) / 10

    total_hours = 0
    for tag in tag_length:
        total_hours += tag_length[tag]

    print("\n\n")

    print("\n-------------------------\n")
    print("Daily AVG: {}".format(avg(day_length) / 60))

    print()
    print("Tag Distribution:{}Issue Distribution:\n".format(' ' * 57))

    magic = 54
    gap = 20 * ' '
    header = " {:^15s} | {:^4s} | {:^9s} | {:^7s} | {:^5s}{} {:^15s} | {:^4s} | {:^6s}".format("Tag", "%", "Length(m)", "AVG(m)", "Count", gap, 'Issue' , '%', 'Length') + gap
    liner = ('=' * magic) + gap + ('=' * 32)
    arr = []

    for kv in sorted(tag_length.items(), key=lambda kv: kv[1], reverse=True):
        tag = kv[0]
        le = kv[1]
        percent = per(total_hours, le)
        c = tag_count[tag]
        av = le / c
        arr.append(" {:^15s} | {:4.1f} | {:^9d} | {:^7.1f} | {:^5d}".format(tag, percent, le, av, c))

    arr2 = []
    for kv in sorted(issue_sum.items(), key=lambda kv: kv[1], reverse=True):
        issue = kv[0]
        le = kv[1]
        percent = per(total_hours, le)
        arr2.append(" {:^15s} | {:4.1f} | {:^6d}".format(issue, percent, le))

    print(header)
    print(liner)
    for i in range(0, max(len(arr), len(arr2))):
        line = arr[i] if len(arr) > i else ' ' * magic
        line += gap
        line += arr2[i] if len(arr2) > i else ' ' * magic
        print(line)

    print('\n\n')


def jira_base_url(hostname) -> str:
    return 'https://{}/rest/'.format(hostname)


def test_jira_connection(hostname, username, password) -> bool:
    r1 = requests.post(jira_base_url(hostname) + 'auth/1/session', json={'username': username, 'password': password})
    jira_config['jar'] = r1.cookies
    r2 = requests.get(jira_base_url(hostname) + 'auth/1/session', cookies=jira_config['jar'])
    print(str(r1.status_code), str(r2.status_code))
    return r2.status_code == 200


def jira_connect() -> bool:
    path = tim_dir + "jira"
    input_flag = False
    if not os.path.exists(path):
        hostname = input('Please enter Jira hostname\n')
        username = input('Please enter Jira username\n')
        password = input('Please enter Jira password\n')
        prefix = input('Please enter Jira prefix\n')
        input_flag = True
    else:
        with open(path, "r") as f:
            hostname = f.readline().strip()
            username = f.readline().strip()
            password = f.readline().strip()
            prefix = f.readline().strip()

    while not test_jira_connection(hostname, username, password):
        if get_yes_no("Jira connection test failed, Retry?"):
            hostname = input('Please enter Jira hostname\n')
            username = input('Please enter Jira username\n')
            password = input('Please enter Jira password\n')
            prefix = input('Please enter Jira prefix\n')
            input_flag = True
        else:
            return False

    print("Jira connection test -> Successful.")
    if input_flag and get_yes_no("Do you want to save Jira credentials ? (SECURITY WARNING: It would be saved in a "
                                 "plain text file in your system"):
        touch(path)
        with open(path, "w") as f:
            f.write(hostname + "\n")
            f.write(username + "\n")
            f.write(password + "\n")
            f.write(prefix)

    jira_config['prefix'] = prefix
    jira_config['host'] = hostname
    return True


def sync_jira(day: int):
    if not jira_connect():
        return
    date = days_ago(day)
    path = date_to_path(date)
    data = load_file(path)
    change_flag = False
    sample = None
    for other in data:
        if sample is not None:
            if sample.message.startswith('#') and not sample.jira_sync and not sample.jira_skip:
                change_flag = True
                sync_jira_sample(date, sample, other)
        sample = other

    if change_flag:
        save_file(data, path)


def sync_jira_sample(file_date: datetime, sample: Sample, other: Sample):
    print("Syncing:")
    print(sample)
    if get_yes_no("Do you want to sync this task with jira?"):

        key = sample.message.split(" ")[0].replace('#', '')
        if "-" not in key:
            key = jira_config['prefix'] + '-' + key

        d = diff(sample, other)
        start_datetime = file_date.replace(hour=sample.hour(), minute=sample.minute()).strftime(
            '%Y-%m-%dT%H:%M:%S.000') + tzname
        message = {
            'comment': sample.message,
            'timeSpentSeconds': (d * 60),
            'started': start_datetime
        }

        url = jira_base_url(jira_config['host']) + 'api/2/issue/{}/worklog'.format(key)
        result = requests.post(url, json=message, cookies=jira_config['jar'])
        if result.status_code == 201:
            sample.jira_sync = True
        else:
            print('WARNING: Could not sync ' + key)
    else:
        sample.jira_skip = True


def print_help():
    print("Tim time tracker, version {}".format(ver))
    print("---------------------------------\n")
    commands = [
        ("-t <MINUTES> <MESSAGE>", "Start activity from <MINUTES> ago"),
        ("<MESSAGE>", "start activity from this moment"),
        ("-tt <MINUTES> <MESSAGE>",
         "Start and finish given activity from <MINUTES> ago, then continue the last activity."),
        ("-o, --open [DAYS_AGO]", "Open log file for specified day in default system editor. default value is 0."),
        ("-s, --summary <START> [END]", "Summarize events from <START> days ago until <END> days ago, inclusive."),
        ("-j, --jira [DAY_AGO]",
         "Sync issues of the given task with jira, an issue is a message that starts with #, default value is 0"),
        ("-r, --review [DAYS_AGO]", "review and add tags to activities. Default value is 0"),
        ("-p, --print [DAYS_AGO]", "Print data file, default value is 0"),
        ("-c, --command tags", "list tags"),
        ("-c, --command add <TAG>", "add a tag."),
        ("-c, --command end", "Add end to the file"),
        ("-h, --help", "print this help"),
    ]
    for command in commands:
        print("" + command[0])
        print("\t" + command[1])
        print()


def run():
    if len(args) == 1:
        cat(now)
        print("")
    else:
        first = args[1]
        if first == '-j' or first == '--jira':
            start = 0
            if len(args) == 2:
                start = 0
            elif len(args) == 3:
                start = int(args[2])
            else:
                print('Expected one numerical argument')
            sync_jira(start)

        elif first == "--summary" or first == '-s':
            if len(args) == 3:
                start = 0
                end = int(args[2])
                summarize(start, end)
            elif len(args) == 4:
                start = int(args[2])
                end = int(args[3])
                if start > end:
                    (start, end) = (end, start)
                summarize(start, end)
            else:
                print('Expected at least one numerical argument')

        elif first == '-r' or first == "--review":
            days = 0
            if len(args) == 3:
                days = int(args[2])
            elif len(args) > 3:
                print('Expected one numerical argument')
                return
            review(days_ago(days))

        elif first == '-o' or first == '--open':
            days = 0
            if len(args) == 3:
                days = int(args[2])
            elif len(args) > 3:
                print('Expected one numerical argument')
                return
            date = days_ago(days)
            path = date_to_path(date)
            open_editor(path)

        elif first == '-p' or first == '--print':
            days = 0
            if len(args) == 3:
                days = int(args[2])
            elif len(args) > 3:
                print('Expected one numerical argument')
                return
            cat(days_ago(days))

        elif first == "-h" or first == "--help":
            print_help()

        elif first == "-c" or first == '--command':
            command = args[2]

            if command == 'tags':
                arr = load_tags()
                print(", ".join(arr))
            elif command == "add":
                if len(args) == 4:
                    add_tag(args[3])
                    arr = load_tags()
                    print(", ".join(arr))
                else:
                    print("Expected One argument after add")
            elif command == "end":
                insert_command("END", today_path, str(now.hour) + ':' + str(now.minute))

        elif args[1] == "-t":
            d = int(args[2])
            message = " ".join(args[3:])
            insert(message, today_path, d)

        elif args[1] == "-tt":
            if len(args) < 4:
                print("Invalid args: t -tt MINUTES MESSAGE")
                return
            time_diff = int(args[2])
            message = " ".join(args[3:])
            samples = load_file(today_path)
            insert(message, today_path, time_diff)
            if len(samples) > 0:
                target = samples[-1]
                insert(target.message, today_path, 0, target.tag)

        else:
            message = " ".join(args[1:])
            if message.startswith('-'):
                print("ERROR: Message cannot start with '-'.")
            else:
                insert(message, today_path, 0)


run()
