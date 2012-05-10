#!/usr/bin/env python
import argparse
import json
import os
import signal
import subprocess
import sys
import time

_NOTIFY = 'growlnotify'
_CONF = os.path.expanduser('~/.doro')
_STATUS = _CONF + '/status'
_LOG = _CONF + '/log'

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


def log_state(state, duration=0):
    now = int(time.time())
    if not os.path.exists(_CONF):
        os.mkdir(_CONF)
    if state != 'done':
        with open(_STATUS, 'w') as f:
            f.write(json.dumps((now, state, duration, now + (duration * 60))))

    with open(_LOG, 'a') as f:
        f.write('{0}, {1}, {2}\n'.format(now, state, duration))


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


def print_status(percent=False):
    res = check_status()
    if not res:
        return
    
    status, pct, left = res
    if percent:
        print "{status} {pct}%".format(
            status=status,
            pct=pct,
        )
    else:
        mins = int(left / 60)
        print "{status} {mins}m".format(
            status=status,
            mins=mins,
        )


def change_state(state, mins=0, **kwargs):
    msg, sticky = _MSGS[state]
    notify(msg.format(mins=mins, **kwargs), sticky)
    log_state(state, mins)
    time.sleep(mins * 60)
    log_state('done')


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
    parser.add_argument('--pct', action="store_true")

    args = parser.parse_args()
    if args.state:
        print_status(args.pct)
    else:
        if check_status():
            print "Already running"
            print_status()
            sys.exit(1)
        run(args.work, args.rest)


if __name__ == '__main__':
    main()
