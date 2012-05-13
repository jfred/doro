#!/usr/bin/env python
import argparse
import json
import os
import signal
import subprocess
import sys
import time

_NOTIFY = ['notify-send', 'growlnotify' 'echo']
_CONF = os.path.expanduser('~/.doro')
_STATUS = _CONF + '/status'
_LOG = _CONF + '/log'
_PID = _CONF + '/pid'

_MSGS = {
    'canceled': ('Pomodoro canceled', True),
    'work': ('Start pomodoro for {mins} minutes', False),
    'rest': ('Rest for {mins} minutes', True),
}


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def notify(msg, sticky=False):
    try:
        notify = (prog for prog in _NOTIFY if which(prog))
        args = [notify.next(), msg]
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
    os.remove(_PID)


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


def test(args):
    notify('testing notification')


def status(args):
    res = check_status()
    if not res:
        print "lazy are we?"
        return

    status, pct, left = res
    if args.pct:
        print "{status} {pct}%".format(
            status=status,
            pct=pct,
        )
    else:
        mins = int(left / 60)
        secs = int(left % 60)
        if mins:
            print "{status} {mins}m".format(
                status=status,
                mins=mins,
            )
        else:
            print "{status} {secs}s".format(
                status=status,
                secs=secs,
            )


def change_state(state, mins=0, **kwargs):
    msg, sticky = _MSGS[state]
    notify(msg.format(mins=mins, **kwargs), sticky)
    log_state(state, mins)
    time.sleep(mins * 60)
    log_state('done')


def run(args):
    if check_status():
        print "Already running"
        status()
        sys.exit(1)

    def signal_handler(sig, frame):
        if sig == signal.SIGINT:
            change_state('canceled')
        elif sig == signal.SIGQUIT:
            log_state('done - force')
        clear_state()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    change_state('work', args.work)
    change_state('rest', args.rest)
    clear_state()


def start(args):
    # have to come up with a better way to run this module
    p = subprocess.Popen([
        'python',
        sys.argv[0],
        '-w', str(args.work),
        '-r', str(args.rest),
        'force'
    ])
    with open(_PID, 'w') as f:
        f.write(str(p.pid))


def send_signal(sig):
    if not os.path.exists(_PID):
        print "Not running"
        sys.exit(1)
    with open(_PID, 'r') as f:
        pid = f.read()
    subprocess.Popen(['kill', '-s', sig, pid])


def cancel(args):
    send_signal('INT')


def done(args):
    send_signal('QUIT')

_cmds = {
    "start": start,
    "done": done,
    "cancel": cancel,
    "stop": cancel,
    "force": run,
    "status": status,
    "test": test,
}


def main():
    parser = argparse.ArgumentParser(
            description="Pomodoro on the command line")
    parser.add_argument('-w', '--work', type=float, default=25,
            help="minutes to work"
            )
    parser.add_argument('-r', '--rest', type=float, default=5,
            help="minutes to rest"
            )
    parser.add_argument('command',
            choices=_cmds.keys(),
            default="start",
            )
    parser.add_argument('-p', '--pct',
            action='store_true',
            help="show status in percentage complete",
            )

    args = parser.parse_args()
    _cmds[args.command](args)


if __name__ == '__main__':
    main()
