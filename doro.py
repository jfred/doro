#!/usr/bin/env python
import argparse
import json
import os
import signal
import subprocess
import sys
import time

_NOTIFY = 'growlnotify'
_STATUS = '/Users/jfred/.doro/status'

_MSGS = {
    'canceled': ('Pomodoro canceled', True),
    'work': ('Start pomodoro for {mins} minutes', False),
    'rest': ('Rest for {mins} minutes', True),
}


def notify(msg, sticky=False):
    try:
        args = [_NOTIFY, '-m', msg]
        if sticky:
            args += ['-s', '-p', 'Emergency']
        subprocess.call(args)
    except:
        print msg


def log(state, duration):
    now = time.time()
    with open(_STATUS, 'w') as f:
        f.write(json.dumps((now, state, duration, now + (duration * 60))))


def clear_state():
    os.remove(_STATUS)


def check_status():
    try:
        with open(_STATUS, 'r') as f:
            state = json.loads(f.read())
    except:
        return None
    now = time.time()
    logged, state, duration, end = state
    if now > end:
        return None

    pct = int((now - logged) / (duration * 60) * 100)
    return state, pct, end - now


def print_status(detail=False):
    res = check_status()
    if not res:
        return
    
    status, pct, left = res
    if detail:
        mins = int(left / 60)
        secs = int(left % 60)
        print "{status} ({pct}%) {mins}:{secs:02d}".format(
            status=status,
            pct=pct,
            mins=mins,
            secs=secs,
        )
    else:
        print "{status} ({pct}%)".format(
            status=status,
            pct=pct,
        )


def change_state(state, mins=0, **kwargs):
    msg, sticky = _MSGS[state]
    notify(msg.format(mins=mins, **kwargs), sticky)
    log(state, mins)
    time.sleep(mins * 60)


def run(work, rest, catch=True):
    def signal_handler(signal, frame):
        change_state('canceled')
        clear_state()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    change_state('work', work)
    change_state('rest', rest)
    clear_state()


def main():
    parser = argparse.ArgumentParser(
            description="Pomodoro on the command line")
    parser.add_argument('-w', '--work', type=float, default=25)
    parser.add_argument('-r', '--rest', type=float, default=5)
    parser.add_argument('-s', '--state', action="store_true")

    args = parser.parse_args()
    if args.state:
        print_status()
    else:
        if check_status():
            print "Already running"
            print_status()
            sys.exit(1)
        run(args.work, args.rest)


if __name__ == '__main__':
    main()
