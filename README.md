# Tim the time tracker
## Overview
Tim is an easy to use personal time tracker designed based on daily needs of a regular software developer.
It's core value is simplicity and ease of use to minimize overhead of time-tracking for anyone who can access a terminal in a blink!
Tim is still under development, but note that at it's best , tim is a toy project.

Also note that tim is not designed for night owls! It assumes that you do not work past midnight and anything you do 
past-midnight is logged in the next day's log.

## Requirements
Tim is designed specially for linux users, although it would probably work well on any OS.
* Python (3.6 or above) Is required for core functionality
* python's __requests__ module is required for Jira integration 

## Installation
Currently tim is too small and simple to have an installer! So just make sure that you have the requirements and clone 
repo.  Then make your appropriate symbolic link (shortcut) somewhere in your $PATH to __tim.py__ file. e.g:
```bash
sudo ln -s /PATH/TO/tim.py /usr/local/bin/t
``` 
Since the aim of using tim is minimizing the overhead, it's highly recommended to name your link __t__ .

Also if you want to use Jira integration, you're gonna need python requests which can be installed with your package-manager or __pip__.

## Basic Usage

### Managing tags
First of all, add your tags :
```bash
t -c add development
t -c add rest
t -c add server_maintenance
# etc.. 
```
Don't worry about long tag names, tagging is supported by auto-complete feature. Next you can checkout your tags using :

```bash
t -c tags
```
Note that you can manually manage your tags, it's a plain text file. Tim stores it's data in
```bash
~/.config/tim
```
where you can find a __tags__ file and change it as you please.

### Starting an activity
Now you can easily use tim. to add a message just write your message after __t__ command:
```bash
t Something is going on
```
The time span is calculated from the moment that you entered this activity until you enter another activity in tim.
There are multiple ways to add an activity to tim.

### Start an activity in the past 
One of the features that is used regularly is __t -t minutes__ which is used when you change your activity and after a 
while you remember that you forgot to enter it in __tim__ , for example you start working on another issue and after 14 minutes
you remember that you did not enter it in tim, so you :
```bash
t -t 14 something else
```  
This command adds the new activity , but set's it's start point 14 minutes ago.

### Start and end activity in the past and continue your previous activity 

Another case is where the middle of __activity 1__, something else distracts you, for example a server catches on fire! and you 
forget to add this new activity to tim. finally the fire is dealt with and you come back to __activity 1__ and you realize that you 
were dealing with fire for approximately 25 minutes without adding it to tim and now you are resuming your previous activity .
So you :
```bash
t -tt 25 dealing with fire
``` 
which adds __dealing with fire__ to your activities starting 25 minutes ago and then adds your previous activity starting now.

### Review and tag your activity
If you execute __t__ without any parameter it prints today's activity. If you want to tag your activities Just use review command : 
```bash
t -r
# or
t --review
```
It reviews your activities and asks you to enter a tag wherever a tag is not present.
You can pass a parameter to review command to review a previous day's activities:
```bash
t -r 2 
```
this sample reviews activities which was recorded two days ago.


Basic usage is demonstrated in this video :
![Video guide](https://user-images.githubusercontent.com/4332421/47564942-a46d8300-d933-11e8-8441-33d0833e144a.gif)

### Jobs and issues
You summarize and analyze your data using tags not messages. Jobs are just meaningless messages, without tags you can't
do anything with them.

When a __#__ is added in front of an activity message, it becomes an issue, which is basically an activity with a specific meaning.
Issues are summarized and analyzed parallel to regular activities (you can see this in summary mode).
So issues add another level to your data. For example, you log three activities: __#issue-1 , #issue-2 and #issue-1__  
(each of which took 1 hour)and then tag all of them as development. Now when you summarize your data, you will see that 
you have three hours of development, and also two hours for __#issue-1__  and one hour for __#issue-2__.

### End of the day
Make sure you end your daily log with __-e__ or __--end__. It adds a special flag to your log, which means that the last
activity is done and there won't be any more activities in this day.

## Jira integration
Tim can send work-log of your __issues__ to Jira (it's tested against Jira Server version 7.12).
First you need to mark your activities with desired Jira issue key. For example, imagine that you are working on a Jenkins for 
issue #PRJ-5122 (it's a Jira issue id). You can track it like this: (Later you can tag it with whatever you want. )
```bash
t #PRJ-5122 just hacking around the jenkins
```
You can track all your issues like this and at the end of the day you can send the log to jira with
```bash
t -j
```
You can also sync a previous day with Jira server by adding a numeric parameter (days ago, 1 is yesterday) to the above 
command.
The first time that you run a jira command it asks you your username and password (and an issue prefix) and stores them in a plain text file
if you want (WARNING).
The issue prefix is the code name of a Jira project (like PRJ in #PRJ-5122) that you work on the most, so that every time 
you write an issue ID like __#5122__ instead of __#PRJ-5122__ it automatically adds the common prefix to issue id.

## All commands
Use __t --help__ to see all commands and combinations.
```TEXT
<MESSAGE>
	start activity from this moment

-tt <MINUTES> <MESSAGE>
	Start and finish given activity from <MINUTES> ago, then continue the last activity.

-o, --open [DAYS_AGO]
	Open log file for specified day in default system editor. default value is 0.

-s, --summary <START> [END]
	Summarize events from <START> days ago until <END> days ago, inclusive.

-j, --jira [DAY_AGO]
	Sync issues of the given task with jira, an issue is a message that starts with #, default value is 0

-r, --review [DAYS_AGO]
	review and add tags to activities. Default value is 0

-p, --print [DAYS_AGO]
	Print data file, default value is 0

-c, --command tags
	list tags

-c, --command add <TAG>
	add a tag.

-c, --command end
	Add end to the file

-h, --help
	print this help

``` 
